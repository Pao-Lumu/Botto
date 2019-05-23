import asyncio
import datetime
import itertools
import os
import re
import socket
import textwrap
from concurrent import futures

import aiofiles
import discord
import mcrcon
import valve
import valve.source
from mcstatus import MinecraftServer as mc
from valve import rcon
from valve.source.a2s import ServerQuerier as src

from utils import sensor as sensor


class Game:

    def __init__(self, bot):
        self.bot = bot

    async def check_server_running(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            data = sensor.get_running()
            if data:
                self.bot._game_stopped.clear()
                await asyncio.sleep(2)
                self.bot._game_running.set()
                await self.bot.wait_until_game_stopped()
            else:
                await asyncio.sleep(5)

    async def check_server_stopped(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            data = sensor.get_running()
            if not data:
                self.bot._game_running.clear()
                await asyncio.sleep(2)
                self.bot._game_stopped.set()
                await self.bot.wait_until_game_running()
            else:
                await asyncio.sleep(5)

    async def get_current_server_status(self):
        await self.bot.wait_until_ready(1)
        self.bot.game, self.bot.gwd = ("", "")
        while not self.bot.is_closed():
            d = sensor.get_running()
            # If no game is running upon instantiation:
            if not d:
                self.bot.game, self.bot.gwd, self.bot.gameinfo = ("", "", "")
                await self.bot.change_presence()
                self.bot.bprint("Server Status | All Servers Offline")
                await self.bot.wait_until_game_running()
            # Elif game is running upon instantiation
            else:
                data = sensor.get_game_info()
                self.bot.game = data["name"] if data["name"] else "A Game"
                self.bot.gwd = data["folder"]
                self.bot.gameinfo = data
                version = ""
                if "minecraft" in self.bot.gwd:
                    version = data["version"]
                    failure_number = 0
                    while not version and failure_number <= 3:
                        version, failure_number = self.lookup_mc_server("localhost:22222", failure_number)
                        await asyncio.sleep(3)
                gamename = str(self.bot.game) + " " + version
                self.bot.bprint(f"Server Status | Now Playing: {gamename}")
                await self.set_bot_status(gamename, '', '')

                await self.bot.wait_until_game_stopped()

    def lookup_mc_server(self, address, fails):
        try:
            server = mc.lookup(address)
            status = server.query()
            return " " + status.software.version, 0
        except socket.timeout:
            print("Minecraft | Connection To Server Reached Timeout Without Response")
            return "", False
            pass
        except ConnectionRefusedError:
            print("Minecraft | Query Connection Refused")
            return " ", fails + 1
            pass
        except Exception as e:
            print("Minecraft | Server Status Query Exception caught: " + str(e))
            return None, fails + 1
            pass
        except:
            print("uh ok")

    async def set_bot_status(self, line1: str, line2: str, line3: str, *args, **kwargs):
        padder = [line1.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line1))))
                  + line2.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line2))))
                  + line3.replace(' ', '\u00a0')]
        await self.bot.change_presence(activity=discord.Game(f"{' '.join(padder)}"))

    async def send_from_game_to_guild(self):
        await self.bot.wait_until_game_running(10)
        while not self.bot.is_closed():
            if "minecraft" in self.bot.gwd:
                fpath = os.path.join(self.bot.gwd, "logs", "latest.log") if os.path.exists(
                    os.path.join(self.bot.gwd, "logs", "latest.log")) else os.path.join(self.bot.gwd, "server.log")
                server_filter = re.compile(
                    "FO\]:?(?:.*tedServer\]:)? (\[[^\]]*: .*\].*|(?<=]:\s).* joined the game|.* left the game|.* has made the .*)")
                player_filter = re.compile("FO\]:?(?:.*tedServer\]:)? (\[Server\].*|<.*>.*)")
                while "minecraft" in self.bot.gwd:
                    await self.read_server_log(fpath, player_filter, server_filter)

            else:
                await asyncio.sleep(15)

    async def read_server_log(self, fpath, player_filter, server_filter):
        async with aiofiles.open(fpath) as log:
            await log.seek(0, 2)
            size = os.stat(fpath)
            while "minecraft" in self.bot.gwd:
                try:
                    lines = await log.readlines()  # Returns instantly
                    msgs = list()
                    for line in lines:
                        raw_playermsg = re.findall(player_filter, line)
                        raw_servermsg = re.findall(server_filter, line)

                        if raw_playermsg:
                            x = self.check_for_mentions(raw_playermsg)
                            msgs.append(x)
                        elif raw_servermsg:
                            msgs.append(f'`{raw_servermsg[0].rstrip()}`')
                        else:
                            continue
                    if msgs:
                        x = "\n".join(msgs)
                        await self.bot.chat_channel.send(f'{x}')
                    for msg in msgs:
                        self.bot.bprint(f"{self.bot.game} | {msg}")
                    continue
                except NameError:
                    await asyncio.sleep(.75)
                    if size < os.stat(fpath):
                        size = os.stat(fpath)
                    else:
                        break
                    continue

    def check_for_mentions(self, raw_playermsg):
        message = raw_playermsg[0]
        index = message.find('@')
        if index >= 0:
            try:
                mention = message[index + 1:]
                length = len(mention) + 1
                for ind in range(0, length):
                    member = discord.utils.get(self.bot.chat_channel.guild.members, name=mention[:ind])
                    if member:
                        message = message.replace("@" + mention[:ind], f"<@{member.id}>")
                        break
                else:
                    pass
            except Exception as e:
                self.bot.bprint("ERROR | Server2Guild Exception caught: " + str(e))
                pass
        return message

    def check(self, m):
        return m.channel == self.bot.chat_channel

    async def send_from_guild_to_game(self):
        await self.bot.wait_until_game_running(20)
        while not self.bot.is_closed():
            last_reconnect = datetime.datetime(1, 1, 1)
            password = self.bot.gameinfo["rcon"] if self.bot.gameinfo["rcon"] else self.bot.cfg["default_rcon_password"]
            if "minecraft" in self.bot.gwd:
                rcon = mcrcon.MCRcon("127.0.0.1", password, 22232)
                while "minecraft" in self.bot.gwd:
                    try:
                        msg = await self.bot.wait_for('message', check=self.check, timeout=5)
                        if not hasattr(msg, 'author') or (hasattr(msg, 'author') and msg.author.bot):
                            pass
                        elif msg.clean_content:
                            time_sec = (datetime.datetime.now() - last_reconnect)
                            if time_sec.total_seconds() >= 240:
                                last_reconnect = datetime.datetime.now()
                                rcon.connect()
                            if msg.clean_content[0] == '/' and msg.author.id == self.bot.application_info().owner.id:
                                x = rcon.command(msg.clean_content)
                                if x:
                                    await self.bot.chat_channel.send(f'`{x}`')
                            else:
                                command = f"say §9§l{msg.author.name}§r: {msg.clean_content}"
                                if len(command) >= 100:
                                    wrapped = textwrap.wrap(msg.clean_content, 86 + len(msg.author.name))
                                    for r in wrapped:
                                        rcon.command(f"say §9§l{msg.author.name}§r: {r}")
                                else:
                                    rcon.command(command)
                                    self.bot.bprint(f"Discord | <{msg.author.name}>: {msg.clean_content}")
                        if msg.attachments:
                            rcon.command(f"say §l{msg.author.name}§r: File {msg.attachments[0]['filename']}")
                            self.bot.bprint(f"Discord | {msg.author.name}: File {msg.attachments[0]['filename']}")
                    except socket.error as e:
                        rcon.disconnect()
                        self.bot.bprint(f"Socket error: {e}")
                        pass
                    except futures.TimeoutError:
                        pass
            elif "gmod" in self.bot.gwd:
                with valve.rcon.RCON(("192.168.25.40", 22222), password) as rcon:
                    while "gmod" in self.bot.gwd:
                        try:
                            msg = await self.bot.wait_for('message', check=self.check, timeout=5)
                            if not hasattr(msg, 'author') or (hasattr(msg, 'author') and msg.author.bot):
                                pass
                            elif msg.clean_content:
                                i = len(msg.author.name)
                                if len(msg.clean_content) + i > 243:
                                    wrapped = textwrap.wrap(msg.clean_content, 243 - i)
                                    for r in wrapped:
                                        rcon(f"say {msg.author.name}: {msg.clean_content}")
                                else:
                                    rcon(f"say {msg.author.name}: {msg.clean_content}")
                                self.bot.bprint(f"Discord | <{msg.author.name}>: {msg.clean_content}")
                            if msg.attachments:
                                rcon.command(f"say §l{msg.author.name}§r: Image {msg.attachments[0]['filename']}")
                                self.bot.bprint(
                                    f"Discord | {msg.author.name}: Image {msg.attachments[0]['filename']}")
                        except futures.TimeoutError:
                            pass
            else:
                await asyncio.sleep(5)

    async def update_server_information(self):
        await self.bot.wait_until_ready(20)
        while not self.bot.is_closed():
            if not self.bot.game:
                if self.bot.chat_channel.topic:
                    await self.bot.chat_channel.edit(topic="")
                await self.bot.wait_until_game_running()
                await asyncio.sleep(5)
            elif "minecraft" in self.bot.gwd:
                tries = 1
                server = mc.lookup("localhost:22222")
                failed = False
                version = ''
                mod_count = ''
                player_count = ''
                while "minecraft" in self.bot.gwd:
                    try:
                        stats = server.status()
                        version, online, max = stats.version.name, stats.players.online, stats.players.max
                        if 'modinfo' in stats.raw:
                            mod_count = f"{len(stats.raw['modinfo']['modList'])} mods installed"
                        else:
                            mod_count = 'Vanilla'

                        player_count = f"({online}/{max} players)" if not failed else ""
                        if failed:
                            stats = server.query()
                            version, online, max = stats.software.version, stats.players.online, stats.players.max
                            player_count = f"({online}/{max} players)" if not failed else ""
                        cur_status = f"Playing: Minecraft {version} {player_count}"
                        await self.bot.chat_channel.edit(topic=cur_status)
                        await self.set_bot_status(f'{self.bot.game} {version}', mod_count, player_count)
                    except BrokenPipeError:
                        self.bot.bprint("Server running a MC version <1.7, or is still starting. (BrokenPipeError)")
                        await self.sleep_with_backoff(tries)
                        tries += 1
                        break
                    except ConnectionRefusedError:
                        self.bot.bprint("Server running on incorrect port. (ConnectionRefusedError)")
                        break
                    except ConnectionResetError:
                        self.bot.bprint("Connection to server was reset by peer. (ConnectionResetError)")
                        failed = True
                        pass
                    except discord.Forbidden:
                        self.bot.bprint("Bot lacks permissions to edit channels. (discord.Forbidden)")
                        pass
                    except ConnectionError:
                        self.bot.bprint("General Connection Error. (ConnectionError)")
                    except socket.timeout:
                        self.bot.bprint("Server not responding. (socket.timeout)")
                        failed = True
                    except NameError:
                        pass
                    except Exception as e:
                        self.bot.bprint(f"Failed with Exception {e}")
                        failed = True
                        pass
                    except:
                        self.bot.bprint("Failed with unknown error")
                        failed = True
                        pass
                    finally:
                        await asyncio.sleep(30)
            elif "gmod" in self.bot.gwd:
                while "gmod" in self.bot.gwd:
                    try:
                        with src(('192.168.25.40', 22222)) as server:
                            info = server.info()
                            players = server.players()
                        mode = info["game"]
                        map = info["map"]
                        cur = info["player_count"]
                        max = info["max_players"]
                        cur_status = f"Playing: Garry's Mod - {mode} on map {map} ({cur}/{max} players)"
                        await self.bot.chat_channel.edit(topic=cur_status)
                        await self.set_bot_status("Garry's Mod", f"{mode} on map {map}", f"({cur}/{max} players)")
                    except discord.Forbidden:
                        print("Bot lacks permission to edit channels. (discord.Forbidden)")
                    except valve.source.NoResponseError:
                        print("No Response from server before timeout (NoResponseError)")
                    except Exception as e:
                        print(f"Error: {e} {type(e)}")
                    await asyncio.sleep(30)
            else:
                await asyncio.sleep(30)

    async def sleep_with_backoff(self, tries, default=5):
        await asyncio.sleep(default * tries)
