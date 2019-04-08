import asyncio
import datetime
import json
import logging
import os
import socket
import sys
import traceback
import random
import re

import discord
from discord.ext import commands

import botto
import valve
import mcrcon
import aiofiles
from mcstatus import MinecraftServer as mc

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='botto.log', encoding='utf-8', mode='r+')
log.addHandler(handler)

initial_extensions = [
    'modules.admin'
]

bot = botto.Botto(command_prefix="]", cog_folder="modules")


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(
            error.original), file=sys.stderr)


@bot.event
async def on_ready():
    bot.chat_channel = bot.get_channel("491059677325557771")
    print('------------------')
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------------------')
    print("Primary Chat Channel: " + bot.chat_channel.name)
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()


async def get_current_server_status():
    await bot.wait_until_ready()
    bot.game, bot.gwd = ("", "")
    while not bot.is_closed:
        proc = await asyncio.create_subprocess_shell("/usr/bin/python3 ~/Botto/sensor.py", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        raw = await proc.communicate()
        p = raw[0].decode("utf-8").rstrip().split('\n')
        if p[0] == bot.game:
            pass
        elif not p[0]:
            bot.game, bot.gwd, bot.game_version = ("", "", "")
            await bot.change_presence()
            print("Server Status | Stopped All Servers")
        elif bot.game != p[0]:
            bot.game = p[0]
            bot.gwd = " ".join(p[1].split(" ")[1:])
            if bot.game == "Minecraft":
                version = ""
                while not version:
                    version = lookup_mc_server("localhost:22222")
                    print("Version:{}".format(version))
                    await asyncio.sleep(2)
            np = discord.Game(name=str(bot.game) + version)
            bot.game_version = version
            print("Server Status | Now Playing: " + str(bot.game) + version)
            await bot.change_presence(game=np)
        await asyncio.sleep(7.5)


def lookup_mc_server(address):
    try:
        server = mc.lookup(address)
        status = server.query()
        return " " + status.software.version
    except socket.timeout:
        print("Minecraft | Connection To Server Reached Timeout Without Response")
        return " "
    except ConnectionRefusedError:
        print("Minecraft | Query Connection Refused")
        return " "
    except Exception as e:
        print("Minecraft | Server Status Query Exception caught: " + str(e))
        return None


async def send_from_server_to_discord():
    await bot.wait_until_ready()
    await asyncio.sleep(1)
    while not bot.is_closed:
        if bot.game == "Minecraft":
            fpath = os.path.join(bot.gwd, "logs", "latest.log")
            if not os.path.exists(fpath):
                fpath=os.path.join(bot.gwd, "server.log")
            async with aiofiles.open(fpath, loop=bot.loop) as log:
                await log.seek(0,2)
                while bot.game == "Minecraft":
                    line = await log.readline()
                    if not line:
                        await asyncio.sleep(.5)
                        continue
                    pattern = re.compile("INFO\]:? (\[.*: .*\].*|\[Server\].*|\<.*\>.*|.* joined the game|.* left the game)")
                    raw_message = re.findall(pattern, str(line))
                    line = ""
                    if raw_message:
                        message = raw_message[0]
                        if message.find('@') >= 0:
                            try:
                                index = message.find('@')
                                mention = message[index+1:]
                                length = len(mention)+1
                                for ind in range(0, length):
                                    member = discord.utils.get(bot.chat_channel.server.members, name=mention[:ind])
                                    if member:
                                        print(member.id)
                                        message = message.replace("@" + mention[:ind], "<@{}>".format(member.id))
                                        break
                            except Exception as e:
                                print("ERROR | Server2Discord Exception caught: " + str(e))
                                pass
                                
                        print("{}: {}".format(bot.game, message))
                        await bot.send_message(bot.chat_channel, message)
                        continue
        else:
            await asyncio.sleep(15)


async def send_from_discord_to_server():
    await bot.wait_until_ready()
    await asyncio.sleep(2)
    while not bot.is_closed:
        if bot.game == "Minecraft":
            with mcrcon.MCRcon("127.0.0.1", "ogboxrcon", 22232) as rcon:
                while bot.game == "Minecraft":
                    msg = await bot.wait_for_message(channel=bot.chat_channel, timeout=5)
                    if msg:
                        if not msg.author.bot:
                            rcon.command("""say §l{}§r: §o{}§r""".format(msg.author.name, msg.clean_content))
                            # rcon.command("""say {}: {}""".format(msg.author.name, msg.clean_content))
                            print("Discord: {}: {}".format(msg.author.name, msg.clean_content))
                    else:
                        pass
        else:
            await asyncio.sleep(15)


async def update_channel_description():
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    cur_status = ""
    while not bot.is_closed:
        if not bot.game:
            if bot.chat_channel.topic:
                await bot.edit_channel(bot.chat_channel, topic="")
                cur_status = ""
            await asyncio.sleep(5)
        elif bot.game == "Minecraft":
            server = mc.lookup("localhost:22222")
            while bot.game == "Minecraft":
                try:
                    stats = server.query()
                    online = stats.players.online
                    max = stats.players.max
                    version = stats.software.version
                    not_failed = True
                except ConnectionRefusedError:
                    try:
                        stats = server.status()
                        online = stats.players.online
                        max = stats.players.max
                        version = stats.version.name
                        not_failed = True
                    except socket.timeout:
                        print("Minecraft | Server Query Failed. Defaulting.")
                        player_count = ""
                        version = ""
                        not_failed = False
                finally:
                    player_count = "({}/{} players)".format(online, max) if not_failed else ""
                    cur_status = "Playing: Minecraft {} {}".format(version, player_count)
                    # (Modded or not, MC Version, players online, max players)
                try:
                    await bot.edit_channel(bot.chat_channel, topic=cur_status)
                except discord.Forbidden as e:
                    print("HELP. ME.")
                    pass
                await asyncio.sleep(30)
        else:
            await asyncio.sleep(30)


@bot.event
async def on_resumed():
    print('resumed...')


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


def load_credentials():
    if os.path.isfile("credentials.json"):
        with open('credentials.json') as f:
            return json.load(f)
    else:
        log.warning('file "credentials.json" not found; Generating...')
        with open('credentials.json', 'w+') as f:
            f.write(json.dumps({'token': '', 'client_id': ''}))
        print('Please input your bot\'s credentials and restart.')


if __name__ == '__main__':
    credentials = load_credentials()
    debug = any('debug' in arg.lower() for arg in sys.argv)
    if debug:
        bot.command_prefix = '$'
        token = credentials['debug_token']
        bot.client_id = credentials['debug_client_id']
    else:
        token = ""
        try:
            token = credentials['token']
        except TypeError:
            log.critical('auth token not defined')

    try:
        bot.client_id = credentials['client_id']
    except TypeError:
        log.critical('client id not defined')

    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(
                extension, type(e).__name__, e))
            log.error('Failed to load extension {}\n{}: {}'.format(
                extension, type(e).__name__, e))

    e = True
    while e:
        try:
            bot.loop.create_task(get_current_server_status())
            bot.loop.create_task(send_from_discord_to_server())
            bot.loop.create_task(send_from_server_to_discord())
            bot.loop.create_task(update_channel_description())
            bot.run(token)
        except TimeoutError:
            print("Failed to connect to Discord. Retrying in a few seconds.")

    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
