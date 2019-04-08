#!/usr/bin/env python3

import asyncio
from asyncio.subprocess import PIPE, DEVNULL
import datetime
import json
import logging
import logging.handlers
import os
import socket
import sys
import textwrap
import traceback
import random
import re
import game

import discord
from discord.ext import commands

import botto
import sensor2
import valve
import mcrcon
import aiofiles
from mcstatus import MinecraftServer as mc

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])

# Setup Logging

log = logging.getLogger()
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)

sh = logging.StreamHandler(sys.stderr)
sh.setLevel(logging.CRITICAL)

fmt = logging.Formatter('%(asctime)s - %(message)s', datefmt = "%Y-%m-%d %H:%M:%S")

sh.setFormatter(fmt)
log.addHandler(sh)
discord_logger.addHandler(sh)

initial_extensions = [
      'modules.admin',
      'modules.comrade'
#     'modules.santa'
]

bot = botto.Botto(command_prefix=">", cog_folder="modules")


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
    bot.bprint("Bot started!")
    bot.bprint("""------------------
Logged in as:
Username: {}
ID: {}
Primary Chat Channel: {}
------------------""".format(bot.user.name, bot.user.id, bot.chat_channel.name))
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()

def load_credentials():
    if os.path.isfile("credentials.json"):
        with open('credentials.json') as f:
            return json.load(f)
    else:
        log.warning('file "credentials.json" not found; Generating...')
        with open('credentials.json', 'w+') as f:
            f.write(json.dumps({'token': '', 'client_id': ''}))
        bot.bprint('Please input your bot\'s credentials and restart.')

def load_botconfig():
    if os.path.isfile("botcfg.json"):
        with open('botcfg.json') as f:
            return json.load(f)
    else:
        log.warning('File "botcfg.json" not found; Generating...')
        with open('botcfg.json', 'w+') as f:
            f.write(json.dumps({'chat_channel': '', 'default_rcon_password': ''}))
        print('Please input any relevant information and restart.')


# Bot Event Overrides

@bot.event
async def on_resumed():
    bot.bprint('Resumed...')


@bot.event
async def on_member_update(vor, ab):
    if vor.server.id != "442600877434601472" or vor.bot:
        return
    states = {"status": {"on_set": "came online ({})", "on_update": "changed status from {} to {}",
                         "on_delete": "went offline"},
              "game": {"on_set": "started playing {}", "on_update": "swapped from {} to {}",
                       "on_delete": "stopped playing {}"},
              "nick": {"on_set": "set their nickname to {}", "on_update": "changed their nickname to {}",
                       "on_delete": "deleted their nickname"}}

    for x,y in states.items():
        before = vor.__getattribute__(x)
        after = ab.__getattribute__(x)
        if str(before) == "Spotify" or str(after) == "Spotify":
            return
        if before != after:
            if not before or str(before) == "offline":
                msg = y["on_set"].format(after)
            elif not after or str(after) == "offline":
                msg = y["on_delete"].format(before)
            else:
                msg = y["on_update"].format(before, after)
            log.warning(f"{x.upper()} - {ab.name} {msg}")
            continue

@bot.event
async def on_voice_state_update(vor, ab):
    if vor.server.id != "442600877434601472":
        return
    states = {"deaf": {"on_set": "is now server-deafened",
                       "on_delete": "in no longer server-deafened"},
              "mute": {"on_set": "is now muted",
                       "on_delete": "is no longer server-muted"},
              "self_deaf": {"on_set": "deafened themselves",
                            "on_delete": "undeafened themselves"},
              "self_mute": {"on_set": "muted themselves",
                            "on_delete": "unmuted themselves"},
              "voice_channel": {"on_set": "joined {}", "on_update": "moved from {} to {}",
                                "on_delete": "left {}"}}

    for x,y in states.items():
        before = getattr(vor, x)
        after = getattr(ab, x)
        if before != after:
            if not before:
                msg = y["on_set"].format(after)
            elif not after:
                msg = y["on_delete"].format(before)
            else:
                msg = y["on_update"].format(before, after)
            
            log.warning(f"{x.upper()} - {vor.name} {msg}")
    
    # if ab.voice_channel.id == "442678350272528394":
        # await gulag_em(ab)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id == "442600877434601475" and message.clean_content:
        if message.clean_content[0] != '#':
            await comrade_check(message)
    await bot.process_commands(message)


# Custom methods to simplify code

# async def gulag_em(a):
    # print(dir(a))


async def comrade_check(msg):
    chance = (datetime.datetime.now().timestamp() - bot.cooldown_cyka)/1200 - .05
    if random.random() + chance <= .95:
        return
    if msg.clean_content:
        if msg.clean_content[0] == '>':
            return
    breeki = msg.clean_content.split(" ")
    cyka, blyat = False, False
    vodka = []
    if bot.cooldown_blyat + 3600 < datetime.datetime.now().timestamp():
        blyat = True

    comrades = {"I": "We", "i": "we", "I'm": "We're", "i'm": "we're", "I'll": "We'll", "i'll": "we'll", "I'd": "We'd", "i'd": "we'd", "I've": "We've", "i've": "we've", "my": "our", "mine": "ours", "My": "Our", "Mine": "Ours", "am": "are", "Am": "Are", "Me": "Us", "me": "us"}
    for cheeki in breeki:
        if cheeki in comrades.keys():
            vodka.append("{}".format(comrades[cheeki]))
            cyka = True
        else:
            vodka.append(cheeki)
    if cyka:
        await bot.send_message(msg.channel, "*" + " ".join(vodka) + "\n*Soviet Anthem Plays*")
        bot.cooldown_cyka = datetime.datetime.now().timestamp()
    if msg.author.voice_channel and not msg.author.is_afk and cyka and blyat:
        bot.cooldown_blyat = datetime.datetime.now().timestamp()
        bot.v = await bot.join_voice_channel(msg.author.voice_channel)
        player = bot.v.create_ffmpeg_player("blyat.ogg")
        player.start()
        await asyncio.sleep(25)
        player.stop()
        try:
            await bot.v.disconnect()
        except:
            print("Hey lotus why don't you eat a fucking dick")
   

if __name__ == '__main__':
    credentials = load_credentials()
    botcfg = load_botconfig()
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


    d = str(datetime.date.today())
    log_path = os.path.join("logs", "ogbot.log")
    if not os.path.exists(log_path):
        with open(log_path, "x") as f:
            pass

    fh = logging.handlers.TimedRotatingFileHandler(filename=log_path, when="midnight", encoding='utf-8')
    discord_logger.addHandler(fh)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    gms = game.Game(bot)
    bot.loop.create_task(gms.get_current_server_status())
    bot.loop.create_task(gms.send_from_discord_to_server())
    bot.loop.create_task(gms.send_from_server_to_discord())
    bot.loop.create_task(gms.update_channel_description())
    bot.loop.create_task(gms.check_server_running())
    bot.loop.create_task(gms.check_server_stopped())

    bot.cfg = botcfg
    bot.run(token)
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)


#     if message.author.id == "538196392288452620" and "@​everyone" in message.clean_content:
#         aero_hmm = """Aero: Before you ping everyone, think.
# Is this urgent enough that everyone needs to know ASAP?
# Or can I just put it in chat *without* the tag and let people respond to it as they're able, rather than disturbing them?
# 
# I respect your right to get everyone's attention, which is why I made this, rather than removing the ability for you to ping everyone entirely.
# And, if what you put in the above message IS truly urgent, then I sincerely apologize.
# 
# But unless it's something that pertains to everyone, or something very, VERY important, it's usually better to just leave out the mention."""
#         await bot.send_message(message.channel, aero_hmm)
