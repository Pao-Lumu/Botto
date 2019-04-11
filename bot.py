#!/usr/bin/env python3

import asyncio
import datetime
import json
import logging.handlers
import os
import random
import sys
import traceback
import discord

from discord.ext import commands

import ogbot_base
import game

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])

# Setup Logging

log = logging.getLogger()
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)

sh = logging.StreamHandler(sys.stderr)
sh.setLevel(logging.CRITICAL)

fmt = logging.Formatter('%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

sh.setFormatter(fmt)
log.addHandler(sh)
discord_logger.addHandler(sh)

initial_extensions = [
    'modules.admin',
    'modules.comrade'
]

bot = ogbot_base.Botto(command_prefix=">", cog_folder="modules")


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.message.author.send('This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await ctx.message.author.send('Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(
            error.original), file=sys.stderr)


@bot.event
async def on_ready():
    # bot.chat_channel = bot.get_channel(491059677325557771)
    bot.chat_channel = {"name": 'xd'}
    bot.bprint("Bot started!")
    print(dir(bot))
    print(bot.user.name)
    print(bot.chat_channel)
    bot.bprint("""------------------
Logged in as:
Username: {}
ID: {}
Primary Chat Channel: {}
------------------""".format(bot.user.name, bot.user.id, bot.chat_channel))

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
    if vor.guild.id != 442600877434601472 or vor.bot:
        return



    states = {"status": {"on_set": "came online ({})", "on_update": "changed status from {} to {}",
                         "on_delete": "went offline"},
              "activities": {'playing': {"on_set": "started playing {}", "on_update": "swapped from {} to {}",
                           "on_delete": "stopped playing {}"}},
              "nick": {"on_set": "set their nickname to {}", "on_update": "changed their nickname to {}",
                       "on_delete": "deleted their nickname"}}



@bot.event
async def on_voice_state_update(member, vor, ab):
    if member.guild.id != 442600877434601472:
        return
    states = {"deaf": {"on_set": "is now server-deafened",
                       "on_delete": "in no longer server-deafened"},
              "mute": {"on_set": "is now muted",
                       "on_delete": "is no longer server-muted"},
              "self_deaf": {"on_set": "deafened themselves",
                            "on_delete": "undeafened themselves"},
              "self_mute": {"on_set": "muted themselves",
                            "on_delete": "unmuted themselves"},
              "channel": {"on_set": "joined {}", "on_update": "moved from {} to {}",
                                "on_delete": "left {}"}}

    for x, y in states.items():
        before = getattr(vor, x)
        after = getattr(ab, x)
        if before != after:
            if not before:
                msg = y["on_set"].format(after)
            elif not after:
                msg = y["on_delete"].format(before)
            else:
                msg = y["on_update"].format(before, after)

            log.warning(f"{x.upper()} - {member.name} {msg}")
#

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)


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
    bot.loop.create_task(gms.update_server_information())
    bot.loop.create_task(gms.check_server_running())
    bot.loop.create_task(gms.check_server_stopped())

    bot.cfg = botcfg
    bot.run(token)
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
