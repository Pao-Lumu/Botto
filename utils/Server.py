import asyncio
import datetime
import itertools
import os
import socket
import textwrap
from concurrent import futures
from os import path

import aiofiles
import discord
import mcrcon
import psutil
import regex
import valve.rcon as valvercon
import valve.source
from discord import Forbidden
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
        self.last_reconnect = datetime.datetime(1, 1, 1)

        self.bot.loop.create_task(self._rcon_loop())
        self.bot.loop.create_task(self.chat_from_server_to_discord())
        self.bot.loop.create_task(self.chat_to_server_from_discord())
        self.bot.loop.create_task(self.update_server_information())

    def __repr__(self):
        return "a game"

    def is_running(self):
        return self.proc.is_running()

    async def _rcon_loop(self): pass

    async def _log_loop(self): pass

    async def chat_from_server_to_discord(self): pass

    async def chat_to_server_from_discord(self): pass

    async def update_server_information(self):
        print("server")
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

    async def _rcon_connect(self):
        if not self.rcon:
            self.rcon = mcrcon.MCRcon(self.ip, self.password, port=self.rcon_port)
        try:
            time_sec = (datetime.datetime.now() - self.last_reconnect)
            async with self.rcon_lock:
                if time_sec.total_seconds() >= 600:
                    try:
                        self.rcon.connect()
                        self.last_reconnect = datetime.datetime.now()
                    except mcrcon.MCRconException as e:
                        print(e)
        except Exception as e:
            print(e)
            pass

    async def chat_from_server_to_discord(self):
        fpath = path.join(self.working_dir, "logs", "latest.log") if path.exists(
            path.join(self.working_dir, "logs", "latest.log")) else os.path.join(self.working_dir, "server.log")
        server_filter = regex.compile(
            r"INFO\]:?(?:.*tedServer\]:)? (\[[^\]]*: .*\].*|(?<=]:\s).* the game|.* has made the .*)")
        player_filter = regex.compile(r"FO\]:?(?:.*tedServer\]:)? (\[Server\].*|<.*>.*)")

        while self.proc.is_running() and not self.bot.is_closed():
            try:
                await self.read_server_log(str(fpath), player_filter, server_filter)
            except Exception as e:
                print(e)

    async def read_server_log(self, fpath, player_filter, server_filter):
        size = os.stat(fpath)
        async with aiofiles.open(fpath) as log:
            await log.seek(0, 2)
            while self.proc.is_running() and not self.bot.is_closed():
                lines = await log.readlines()  # Returns instantly
                msgs = list()
                for line in lines:
                    raw_playermsg = regex.findall(player_filter, line)
                    raw_servermsg = regex.findall(server_filter, line)

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

                if size < os.stat(fpath):
                    size = os.stat(fpath)
                elif size > os.stat(fpath):
                    print("BREAKIN' OUT BOYS!")
                    break
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
                        member = discord.utils.get(self.bot.chat_channel.guild.members, nick=mention[:ind])
                        if member:
                            message = message.replace("@" + mention[:ind], f"<@{member.id}>")
                            break
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
                    await self._rcon_connect()
                    content = regex.sub(r'<(:\w+:)\d+>', r'\1', msg.clean_content).split(
                        '\n')  # splits on messages lines
                    long = False
                    for index, line in enumerate(content):
                        command = f"§9§l{msg.author.name}§r: {line}"
                        if len(command) >= 100:
                            if not index:
                                content[index] = textwrap.wrap(line, width=90,
                                                               initial_indent=f"§9§l{msg.author.name}§r: ")
                            else:
                                content[index] = textwrap.wrap(line, width=90)
                            long = True
                        elif not index:
                            content[index] = command
                        else:
                            content[index] = line
                    if long:
                        content = itertools.chain.from_iterable(content)
                    async with self.rcon_lock:
                        for line in content:
                            x = self.rcon.command(f"say {line}")
                    self.bot.bprint(f"Discord | <{msg.author.name}>: {' '.join(content)}")
            except mcrcon.MCRconException as e:
                print(e)
                await asyncio.sleep(2)
            except socket.error as e:
                print(e)
                await self.bot.chat_channel.send("Message failed to send; the bot is broken, tag Evan", delete_after=10)
                continue
            except futures.TimeoutError:
                pass
            except Exception as e:
                self.bot.bprint("guild2server catchall:")
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
                self.bot.bprint("Server running a MC version <1.7, or is still starting. (BrokenPipeError)")
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
            except ConnectionError:
                self.bot.bprint("General Connection Error. (ConnectionError)")
            except socket.timeout:
                self.bot.bprint("Server not responding. (socket.timeout)")
                failed = True
            except Forbidden:
                self.bot.bprint("Bot lacks permissions to edit channels. (discord.Forbidden)")
                pass
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
        self.log = list()
        self.log_lock = asyncio.Lock()
        self.bot.loop.create_task(self._log_loop())

    def __repr__(self):
        return "Source"

    async def _log_loop(self):
        port = 22242

        transport, protocol = await self.bot.loop.create_datagram_endpoint(
            lambda: SrcdsLoggingProtocol(self.bot.loop.create_task, self._log_callback),
            local_addr=(self.bot.cfg["local_ip"], port))

        try:
            await self.bot.wait_until_game_stopped()
        finally:
            transport.close()

    async def _log_callback(self, message):
        async with self.log_lock:
            self.log.append(message)

    async def chat_from_server_to_discord(self):
        connections = regex.compile(
            r"""(?<=: ")([\w\s]+)(?:<\d><STEAM_0:\d:\d+><.*>") (?:((?:dis)?connected),? (?|address "(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})|(\(reason ".+"?)))""")
        chat = regex.compile(
            r"""(?<=: ")([\w\s]+)(?:<\d><(?:STEAM_0:\d:\d+|Console)><.*>") (|say|say_team) "([^\|].*)\"""")
        while True:
            try:
                lines = []
                async with self.log_lock:
                    if self.log:
                        lines = self.log
                        self.log = []
                msgs = list()
                for line in lines:
                    raw_connectionmsg = regex.findall(connections, line)
                    raw_chatmsg = regex.findall(chat, line)

                    if raw_chatmsg:
                        msgs.append(f"{'[TEAM] ' if raw_chatmsg[0][1] is 'say_team' else ''} *[{raw_chatmsg[0][0]}]*: {raw_chatmsg[0][2]}")
                    elif raw_connectionmsg:
                        msgs.append(f"`{' '.join(raw_connectionmsg[0])}`")
                    else:
                        continue
                if msgs:
                    x = "\n".join(msgs)
                    await self.bot.chat_channel.send(f'{x}')
                for msg in msgs:
                    self.bot.bprint(f"{self.bot.game} | {''.join(msg)}")
                continue
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(.75)

    async def chat_to_server_from_discord(self):
        with valvercon.RCON((self.bot.cfg["local_ip"], 22222), self.password) as rcon:
            while self.proc.is_running() and not self.bot.is_closed():
                try:
                    msg = await self.bot.wait_for('message', check=self.is_chat_channel, timeout=5)
                    if not hasattr(msg, 'author') or (hasattr(msg, 'author') and msg.author.bot):
                        pass
                    elif msg.clean_content:
                        i = len(msg.author.name)
                        if len(msg.clean_content) + i > 242:
                            wrapped = textwrap.wrap(msg.clean_content, 243 - i)
                            for wrapped_line in wrapped:
                                rcon(f"say {msg.author.name}: {wrapped_line}")
                        else:
                            rcon(f"say |{msg.author.name}: {msg.clean_content}")
                        self.bot.bprint(f"Discord | <{msg.author.name}>: {msg.clean_content}")
                    if msg.attachments:
                        rcon.command(f"say |{msg.author.name}: Image {msg.attachments[0]['filename']}")
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
                                              f"CPU: {self.proc.cpu_percent()}% | Mem: {round(self.proc.memory_percent(), 2)}%")
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


class SrcdsLoggingProtocol(asyncio.DatagramProtocol):

    def __init__(self, cb1, cb2):
        self.callback1 = cb1
        self.callback2 = cb2

    def connection_made(self, transport):
        print("Connected to Server")
        self.transport = transport

    def datagram_received(self, packet, addr):
        message = self.parse(packet)
        self.callback1(self.callback2(message))

    def parse(self, packet: bytes):
        packet_len = len(packet)

        if packet_len < 7:
            raise Exception("Packet is too short")

        for i in range(4):
            if packet[i] != int(0xFF):
                raise Exception('invalid header value')

        if packet[packet_len - 1] != int(0x00):
            raise Exception('invalid footer value')

        ptype, offset, footer = packet[4], 5, 2

        if packet[packet_len - 2] != int(0x0a):
            footer = 1

        if ptype != int(0x52):
            raise Exception('invalid packet type ' + hex(ptype))

        message = packet[offset:(packet_len - footer)]

        return message.decode('utf-8').strip()
