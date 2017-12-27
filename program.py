import asyncio
import datetime
import json
import logging
import os
import sys
import traceback
import random

import discord
from discord.ext import commands

import botto
from funcs.bday_loop import BDLoop

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='botto.log', encoding='utf-8', mode='r+')
log.addHandler(handler)

initial_extensions = [
    'modules.pasta',
    'modules.admin',
    'modules.vote',
    'modules.birthday',
    'modules.reactions'
]

bot = botto.Botto(command_prefix="]")


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
    await randomize_presence()
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------')
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()
    print("Starting birthday announcement loop...")
    asyncio.ensure_future(BDLoop(bot).bday_loop(), loop=bot.loop)
    print("Done!")


async def randomize_presence():
    x = random.randint(0, 9)
    presences = ["with fire", "with its food", "Half-Life 3", "Cards Against Humanity", "you like a damn fiddle!",
                 "The Blame Game", "with itself", "by itself", "MCR while crying over a picture of Miki",
                 "its trap card!"]
    await bot.change_presence(game=discord.Game(name=presences[x]))


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
            bot.run(token)
        except TimeoutError:
            print("Failed to connect to Discord. Retrying in a few seconds.")

    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
