#!/usr/bin/env python3

import asyncio
import datetime
import json
import logging.handlers
import os
import sys
import traceback

import discord
import pyfiglet
from discord.ext import commands
try:
    import uvloop
except:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

import game
import ogbot_base
from utils import helpers

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
    'modules.music',
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
    bot.chat_channel = bot.get_channel(botcfg['chat_channel'])
    bot.meme_channel = bot.get_channel(botcfg['comrade_channel'])
    bot.bprint(f"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
{pyfiglet.figlet_format("The OGBot", font='epic')}
Username: {bot.user.name}  |  ID: {bot.user.id}
Chat Channel: {bot.chat_channel}  |  Meme Channel: {bot.meme_channel}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~""")

    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()
    await asyncio.sleep(4)
    bot.cli = ogbot_base.OGBotCmd(bot.loop, bot)
    await bot.cli.start()
    await bot.close()


def load_credentials():
    if os.path.isfile("credentials.json"):
        with open('credentials.json') as f:
            return json.load(f)
    else:
        log.warning('file "credentials.json" not found; Generating...')
        with open('credentials.json', 'w+') as f:
            f.write(json.dumps({'token': '', 'client_id': ''}))
        bot.bprint('Please input your bot\'s credentials and restart.')
        return False


def load_botconfig():
    if os.path.isfile("botcfg.json"):
        with open('botcfg.json') as f:
            return json.load(f)
    else:
        log.warning('File "botcfg.json" not found; Generating...')
        with open('botcfg.json', 'w+') as f:
            f.write(json.dumps({'guild_ids': [], 'chat_channel': 0, 'default_rcon_password': '', 'comrade_channel': 0}))
        print('Please input any relevant information and restart.')
        return False


# Bot Event Overrides

@bot.event
async def on_resumed():
    bot.bprint('Resumed...')


@bot.event
async def on_member_update(vor, ab):
    if vor.guild.id not in bot.cfg['guild_ids'] or vor.bot:
        return
    bef = frozenset(map(lambda x: helpers.MiniActivity(x), vor.activities))
    aft = frozenset(map(lambda x: helpers.MiniActivity(x), ab.activities))
    states = {"status": {"set": "came online ({})", "update": "changed status from {} to {}",
                         "unset": "went offline"},
              "activities": {'playing': {"set": "started playing {}",
                                         "unset": "stopped playing {}"},
                             'streaming': {"set": "is streaming {}",
                                           "unset": "stopped streaming {}"},
                             'listening': {"set": "is listening to {} by {} on Spotify",
                                           "unset": "stopped listening to {}"}},
              "nick": {"set": "Nickname set to {}", "update": "Nickname changed to {}",
                       "unset": "Nickname was deleted"}}
    changes = []
    if vor.status == ab.status:
        pass
    else:
        x = 'status'
        if ab.status is discord.Status.offline:
            changes.append((x, states[x]['unset']))
        elif vor.status is discord.Status.offline:
            changes.append((x, states[x]['set'].format(ab.status)))
        else:
            changes.append((x, states[x]['update'].format(vor.status, ab.status)))

    if bef == aft:
        pass
    else:
        x = 'activities'
        diff = aft.symmetric_difference(bef)
        for a in diff:
            if a.type == discord.ActivityType.listening:
                if a in aft:
                    changes.append((x, states['activities'][a.type.name]['set'].format(
                        *[a.title, a.artist] if hasattr(a, 'title') else [a.name])))
                elif len(diff) % 2 == 1:
                    changes.append((x, states[x][a.type.name]['unset'].format(a.name)))

            elif a.ob in vor.activities:
                changes.append((x, states[x][a.type.name]['unset'].format(a.name)))
            elif a.ob in ab.activities:
                changes.append((x, states['activities'][a.type.name]['set'].format(
                    *[a.title, a.artist] if hasattr(a, 'title') else [a.name])))
            else:
                bot.bprint('evan you should fix your status code')
        else:
            pass

    if vor.nick == ab.nick:
        pass
    else:
        if not vor.nick:
            changes.append(states['nick']['set'].format(ab.nick))
        elif not ab.nick:
            changes.append(states['nick']['unset'])
        else:
            changes.append(states['nick']['update'].format(ab.nick))

    for x, msg in changes:
        log.warning(f"{x.upper()} - {ab.name} {msg}")


@bot.event
async def on_user_update(vor, ab):
    x = zip((vor.avatar, vor.name, vor.discriminator), (ab.avatar, ab.name, ab.discriminator))
    key = ('avatar', 'name', 'discriminator')

    for y, z in enumerate(x):
        if z[0] == z[1]:
            pass
        else:
            msg = f'{vor.name} changed their {key[y]} from {z[0]} to {z[1]}.'
            log.warning(f"{y} - {ab.name} {msg}")
    pass


@bot.event
async def on_voice_state_update(member, vor, ab):
    if member.guild.id != 442600877434601472:
        return
    states = {"deaf": {"set": "is now server-deafened",
                       "unset": "in no longer server-deafened"},
              "mute": {"set": "is now muted",
                       "unset": "is no longer server-muted"},
              "self_deaf": {"set": "deafened themselves",
                            "unset": "undeafened themselves"},
              "self_mute": {"set": "muted themselves",
                            "unset": "unmuted themselves"},
              "channel": {"set": "joined {}", "update": "moved from {} to {}",
                          "unset": "left {}"}}

    for x, y in states.items():
        before = getattr(vor, x)
        after = getattr(ab, x)
        if before != after:
            if not before:
                msg = y["set"].format(after)
            elif not after:
                msg = y["unset"].format(before)
            else:
                msg = y["update"].format(before, after)

            log.warning(f"{x.upper()} - {member.name} {msg}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


if __name__ == '__main__':
    credentials = load_credentials()
    botcfg = load_botconfig()
    if not credentials or not botcfg:
        exit(0)
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
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "x") as f:
            pass

    fh = logging.handlers.TimedRotatingFileHandler(filename=log_path, when="midnight", encoding='utf-8')
    discord_logger.addHandler(fh)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    bot.log = log
    gms = game.Game(bot)
    bot.loop.create_task(gms.get_current_server_status())
    bot.loop.create_task(gms.send_from_guild_to_game())
    bot.loop.create_task(gms.send_from_game_to_guild())
    bot.loop.create_task(gms.update_server_information())
    bot.loop.create_task(gms.check_server_running())
    bot.loop.create_task(gms.check_server_stopped())

    bot.cfg = botcfg
    bot.run(token)
    # handlers = log.handlers[:]
    # for hdlr in handlers:
    #     hdlr.close()
    #     log.removeHandler(hdlr)
