import asyncio
import datetime
import os
import re
import socket
import textwrap
from concurrent import futures

import aiofiles
import discord
import mcrcon
import psutil
import valve.rcon as valvercon
import valve.source
from mcstatus import MinecraftServer as mc
from valve.source.a2s import ServerQuerier as src


class Server:
    def __init__(self, bot, process, *args, **kwargs):
        self.bot = bot
        self.proc = process
        self.name = kwargs.pop('name', 'a game')
        self.ip = kwargs.pop('ip', '127.0.0.1')
        self.port = kwargs.pop('port', '22222')
        self.password = kwargs.pop('rcon') if kwargs['rcon'] else self.bot.cfg["default_rcon_password"]
        self.working_dir = kwargs.pop('folder', '')

        self.rcon_port = kwargs.pop('rcon_port', 22232)
        self.rcon = None
        self.rcon_lock = asyncio.Lock()

        self.bot.loop.create_task(self.chat_from_server_to_discord())
        self.bot.loop.create_task(self.chat_to_server_from_discord())
        self.bot.loop.create_task(self.update_server_information())

    def __repr__(self):
        return "a game"

    async def _rcon_loop(self): pass

    async def _log_loop(self): pass

    async def chat_from_server_to_discord(self): pass

    async def chat_to_server_from_discord(self): pass

    async def update_server_information(self):
        await self.bot.set_bot_status(self.name, "", "")

    async def sleep_with_backoff(self, tries, wait_time=5):
        await asyncio.sleep(wait_time * tries)
        if self.bot.debug:
            self.bot.bprint(f"sleep_with_backoff ~ Done waiting for backoff")

    @property
    def status(self):
        return self.proc

    def is_chat_channel(self, m):
        return m.channel == self.bot.chat_channel


class MinecraftServer(Server):
    def __init__(self, bot, process, *args, **kwargs):
        self.motd = kwargs.pop('motd', "A Minecraft Server")
        super().__init__(bot, process, *args, **kwargs)

    def __repr__(self):
        return "Minecraft"

    async def _rcon_loop(self):
        if not self.rcon:
            self.rcon = mcrcon.MCRcon(self.ip, self.password, self.rcon_port)
        # TODO: MAKE `last_reconnect` SETTABLE FROM OTHER CODE
        last_reconnect = datetime.datetime(1, 1, 1)
        while self.proc.is_running() and not self.bot.is_closed():
            time_sec = (datetime.datetime.now() - last_reconnect)
            if time_sec.total_seconds() >= 240:
                with self.rcon_lock:
                    try:
                        self.rcon.connect()
                    except mcrcon.MCRconException as e:
                        print(e)

    async def chat_from_server_to_discord(self):
        while self.proc.is_running() and not self.bot.is_closed():
            fpath = os.path.join(self.working_dir, "logs", "latest.log") if os.path.exists(
                os.path.join(self.working_dir, "logs", "latest.log")) else os.path.join(self.working_dir, "server.log")
            server_filter = re.compile(
                r"INFO\]:?(?:.*tedServer\]:)? (\[[^\]]*: .*\].*|(?<=]:\s).* the game|.* has made the .*)")
            player_filter = re.compile(r"FO\]:?(?:.*tedServer\]:)? (\[Server\].*|<.*>.*)")
            while self.proc.is_running() and not self.bot.is_closed():
                try:
                    await self.read_server_log(fpath, player_filter, server_filter)
                except asyncio.CancelledError:
                    break

    async def read_server_log(self, fpath, player_filter, server_filter):
        async with aiofiles.open(fpath) as log:
            await log.seek(0, 2)
            size = os.stat(fpath)
            while self.proc.is_running() and not self.bot.is_closed():
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
                        self.bot.bprint(f"{self.bot.game} | {''.join(msg)}")
                    continue
                except NameError:
                    if size < os.stat(fpath):
                        size = os.stat(fpath)
                    else:
                        break
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(e)
                finally:
                    await asyncio.sleep(.75)

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
                    elif mention[:ind].lower() == 'here' or mention[:ind].lower() == 'everyone':
                        message = message.replace("@" + mention[:ind],
                                                  f"{discord.utils.escape_mentions('@' + mention[:ind])}")
                else:
                    pass
            except Exception as e:
                self.bot.bprint("ERROR | Server2Guild Exception caught: " + str(e))
                pass
        return message

    async def chat_to_server_from_discord(self):
        while self.proc.is_running() and not self.bot.is_closed():
            try:
                msg = await self.bot.wait_for('message', check=self.is_chat_channel, timeout=5)
                if not hasattr(msg, 'author') or (hasattr(msg, 'author') and msg.author.bot):
                    pass
                elif msg.clean_content:
                    content = re.sub(r'<(:\w+:)\d+>', r'\1', msg.clean_content).split('\n')  # splits on messages lines
                    for line in content:
                        command = f"say §9§l{msg.author.name}§r: {line}"
                        if len(command) >= 100:
                            wrapped = textwrap.wrap(line, width=90, initial_indent=f"§9§l{msg.author.name}§r: ")
                            with self.rcon_lock:
                                for i, wrapped_line in enumerate(wrapped):
                                    self.rcon.command(f"say {wrapped_line}")
                        else:
                            with self.rcon_lock:
                                self.rcon.command(command)
                        self.bot.bprint(f"Discord | <{msg.author.name}>: {' '.join(content)}")
            except mcrcon.MCRconException as e:
                print(e)
                await asyncio.sleep(2)
            except socket.error as e:
                print(e)
                await self.bot.chat_channel.send("Message failed to send, the bot is probably broken", delete_after=10)
                continue
            except futures.TimeoutError:
                pass
            except Exception as e:
                print("guild2server catchall:")
                print(e)

    async def update_server_information(self):
        tries = 1
        server = mc.lookup("localhost:22222")
        failed = False
        while self.proc.is_running() and not self.bot.is_closed():
            try:
                await asyncio.sleep(10)
                stats = server.status()
                version, online, max_p = stats.version.name, stats.players.online, stats.players.max
                names = []
                if 'sample' in stats.raw['players']:
                    for x in stats.raw['players']['sample']:
                        names.append(x['name'])
                if 'modinfo' in stats.raw:
                    mod_count = f"{len(stats.raw['modinfo']['modList'])} mods installed"
                else:
                    mod_count = 'Vanilla'
                if failed:
                    stats = server.query()
                    version, online, max_p = stats.software.version, stats.players.online, stats.players.max
                player_count = f"({online}/{max_p} players)" if not failed else ""
                cur_status = f"""Playing: Minecraft {version} {player_count}
{'[' if names else ''}{', '.join(names)}{']' if names else ''}"""
                await self.bot.chat_channel.edit(topic=cur_status)
                await self.bot.set_bot_status(f'{self.bot.game} {version}', mod_count, player_count)
            except BrokenPipeError:
                # self.bot.bprint("Server running a MC version <1.7, or is still starting. (BrokenPipeError)")
                await self.sleep_with_backoff(tries)
                tries += 1
                pass
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
            finally:
                await asyncio.sleep(30)


class SourceServer(Server):
    def __init__(self, bot, process: psutil.Process, *args, **kwargs):
        super().__init__(bot, process, *args, **kwargs)

    def __repr__(self):
        return "Source"

    async def chat_from_server_to_discord(self):
        connections = re.compile(r"")
        chat = re.compile(r"")
        cvars = re.compile(r"")

        # connect = r"""Client "CLIENTNAME" connected (IPADDRESS)"""
        # disconnect = r"""Dropped CLIENTNAME from server(REASON)"""
        # chat = """AAAA"""
        while self.proc.is_running() and not self.bot.is_closed():
            for file in self.proc.open_files():
                if os.path.splitext(file.path)[1] == '.log':
                    logpath = file.path
                    break
            else:
                await asyncio.sleep(3)
                continue
            async with aiofiles.open(logpath) as log:
                await log.seek(0, 2)
                log_refresh = datetime.datetime.now() + datetime.timedelta(minutes=10)
                while log_refresh > datetime.datetime.now():
                    try:
                        lines = await log.readlines()  # Returns instantly
                        msgs = list()
                        for line in lines:
                            raw_connectionmsg = re.findall(connections, line)
                            raw_chatmsg = re.findall(chat, line)
                            raw_cvarsmsg = re.findall(cvars, line)

                            if raw_chatmsg:
                                x = self.check_for_mentions(raw_chatmsg)
                                msgs.append(x)
                            elif raw_connectionmsg:
                                msgs.append(f'`{raw_connectionmsg[0].rstrip()}`')
                            elif raw_cvarsmsg:
                                msgs.append(f'`{raw_cvarsmsg[0].rstrip()}`')
                            else:
                                continue
                        if msgs:
                            x = "\n".join(msgs)
                            # await self.bot.chat_channel.send(f'{x}')
                        # for msg in msgs:
                        #     self.bot.bprint(f"{self.bot.game} | {''.join(msg)}")
                        continue
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        print(e)
                    finally:
                        await asyncio.sleep(.75)

        # fpath = os.path.join(self.working_dir, "logs", "latest.log") if os.path.exists(
        #     os.path.join(self.working_dir, "logs", "latest.log")) else os.path.join(self.working_dir, "server.log")
        # server_filter = re.compile(
        #     r"INFO\]:?(?:.*tedServer\]:)? (\[[^\]]*: .*\].*|(?<=]:\s).* the game|.* has made the .*)")
        # player_filter = re.compile(r"FO\]:?(?:.*tedServer\]:)? (\[Server\].*|<.*>.*)")
        # while self.process.is_running():
        #     try:
        #         await self.read_server_log(fpath, player_filter, server_filter)
        #     except asyncio.CancelledError:
        #         break
        pass

    async def chat_to_server_from_discord(self):
        with valvercon.RCON(("192.168.25.40", 22222), self.password) as rcon:
            while self.proc.is_running() and not self.bot.is_closed():
                try:
                    msg = await self.bot.wait_for('message', check=self.is_chat_channel, timeout=5)
                    if not hasattr(msg, 'author') or (hasattr(msg, 'author') and msg.author.bot):
                        pass
                    elif msg.clean_content:
                        i = len(msg.author.name)
                        if len(msg.clean_content) + i > 243:
                            wrapped = textwrap.wrap(msg.clean_content, 243 - i)
                            for wrapped_line in wrapped:
                                rcon(f"say {msg.author.name}: {wrapped_line}")
                        else:
                            rcon(f"say {msg.author.name}: {msg.clean_content}")
                        self.bot.bprint(f"Discord | <{msg.author.name}>: {msg.clean_content}")
                    if msg.attachments:
                        rcon.command(f"say §l{msg.author.name}§r: Image {msg.attachments[0]['filename']}")
                        self.bot.bprint(
                            f"Discord | {msg.author.name}: Image {msg.attachments[0]['filename']}")
                except futures.TimeoutError:
                    pass

    async def update_server_information(self):
        while self.proc.is_running() and not self.bot.is_closed():
            try:
                with src(('192.168.25.40', 22222)) as server:
                    info = server.info()
                mode = info["game"]
                cur_map = info["map"]
                cur_p = info["player_count"]
                max_p = info["max_players"]
                cur_status = f"Playing: Garry's Mod - {mode} on map {cur_map} ({cur_p}/{max_p} players)"

                await self.bot.chat_channel.edit(topic=cur_status)
                await self.bot.set_bot_status("Garry's Mod", f"{mode} on {cur_map} ({cur_p}/{max_p})",
                                              f"CPU: {self.proc.cpu_percent()}% | Mem: {self.proc.memory_percent()}")
            except discord.Forbidden:
                print("Bot lacks permission to edit channels. (discord.Forbidden)")
            except valve.source.NoResponseError:
                print("No Response from server before timeout (NoResponseError)")
            except Exception as e:
                print(f"Error: {e} {type(e)}")
            await asyncio.sleep(30)


def generate_server_object(bot, process, gameinfo: dict) -> Server:
    if 'minecraft' in gameinfo['folder'].lower():
        return MinecraftServer(bot, process, **gameinfo)
    elif 'srcds' in gameinfo['executable'].lower():
        return SourceServer(bot, process, **gameinfo)
    else:
        return Server(bot, process, **gameinfo)
