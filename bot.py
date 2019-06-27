#!/usr/bin/env python3


import asyncio
import datetime
import json
import logging.handlers
import os
import sys
from collections import defaultdict

# noinspection PyPackageRequirements
import discord
import pyfiglet

import game
import ogbot_base
from ogbotcmd import OGBotCmd
from utils import helpers

# import traceback
# from discord.ext import commands
# try:
#     import uvloop
# except:
#     pass
# else:
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


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
    'modules.comrade',
    'modules.server',
    'modules.responder',
    'modules.reminder'
]

bot = ogbot_base.OGBot(command_prefix=">", cog_folder="modules", owner_id=141752316188426241)


# bot = ogbot_base.OGBot(command_prefix=">", cog_folder="modules")


@bot.event
async def on_ready():
    bot.chat_channel = bot.get_channel(botcfg['chat_channel'])
    bot.meme_channel = bot.get_channel(botcfg['comrade_channel'])
    bot.bprint(f"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
{pyfiglet.figlet_format(bot.user.name, font='epic')}
Username: {bot.user.name}  |  ID: {bot.user.id}
Chat Channel: {bot.chat_channel}  |  Meme Channel: {bot.meme_channel}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~""")

    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()
    await asyncio.sleep(4)
    bot.cli = OGBotCmd(bot.loop, bot)
    await bot.cli.start()
    await bot.close()


def load_credentials() -> dict:
    default = {'token': '', 'client_id': ''}

    if os.path.isfile("credentials.json"):
        with open('credentials.json') as creds:
            dd_creds = defaultdict(lambda: "", json.load(creds))
        for k, v in default.items():
            if k not in dd_creds:
                dd_creds.setdefault(k, v)
        with open('credentials.json', 'w') as creds:
            json.dump(dd_creds, creds)
        return dd_creds
    else:
        log.warning('File "credentials.json" not found; Generating...')
        with open('credentials.json', 'w+') as creds:
            json.dump(default, creds)
        bot.bprint('File "credentials.json" not found; Generating...')
        bot.bprint('Please input your bot\'s credentials and restart.')
        return {}


def load_botconfig() -> dict:
    default = {'guild_ids': [], 'chat_channel': 0, 'default_rcon_password': '', 'comrade_channel': 0}

    if os.path.isfile("botcfg.json"):
        with open('botcfg.json') as bcfg:
            dd_bcfg = defaultdict(lambda: "", json.load(bcfg))
        for k, v in default.items():
            if k not in dd_bcfg:
                dd_bcfg.setdefault(k, v)
        with open('botcfg.json', 'w') as creds:
            json.dump(dd_bcfg, creds)
        return dd_bcfg
    else:
        log.warning('File "botcfg.json" not found; Generating...')
        with open('botcfg.json', 'w+') as bcfg:
            json.dump(default, bcfg)
        bot.bprint('File "botcfg.json" not found; Generating...')
        bot.bprint('Please input any relevant information and restart.')
        return {}


def load_json_file(filename: str, default: dict = {}, path: str = "", generate: bool = False) -> dict:
    if path:
        abs_path = os.path.join(path, filename)
    else:
        abs_path = filename
    try:
        with open(abs_path) as file:
            dd_file = defaultdict(lambda: "", json.load(file))
        for k, v in default.items():
            if k not in dd_file:
                dd_file.setdefault(k, v)
        with open(abs_path, 'w') as creds:
            json.dump(dd_file, creds)
        return dd_file
    except FileNotFoundError:
        if generate:
            bot.bprint(f'File "{filename}" not found{" at path " + path if path else ""}; Generating...')
            with open(abs_path, 'w+') as file:
                json.dump(default, file)
            bot.bprint(f'File "{filename}" not found{" at path " + path if path else ""};')
            bot.bprint('Please input any relevant information and restart.')
            return {}

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
    # 0 = set, 1 = unset, 2 = updated
    states = {"status": ["came online ({})", "went offline", "changed status from {} to {}"],
              "nick": ["Nickname set to {}", "Nickname was deleted", "Nickname changed to {}"],
              "activities": {'playing': ["started playing {}", "stopped playing {}"],
                             'streaming': ["is streaming {}", "stopped streaming {}"],
                             'listening': ["is listening to {} by {} on Spotify", "stopped listening to {}"]}}

    changes = []
    if vor.status == ab.status:
        pass
    else:
        ctype = 'status'
        if ab.status is discord.Status.offline:
            changes.append((ctype, states[ctype][1]))
        elif vor.status is discord.Status.offline:
            changes.append((ctype, states[ctype][0].format(ab.status)))
        else:
            changes.append((ctype, states[ctype][2].format(vor.status, ab.status)))

    if bef == aft:
        pass
    else:
        ctype = 'activities'
        diff = aft.symmetric_difference(bef)
        for a in diff:
            if a.type == discord.ActivityType.listening:
                if a in aft:
                    changes.append((ctype, states['activities'][a.type.name][0].format(
                        *[a.title, a.artist] if hasattr(a, 'title') else [a.name])))
                elif len(diff) % 2 == 1:
                    changes.append((ctype, states[ctype][a.type.name][1].format(a.name)))

            elif a.ob in vor.activities:
                changes.append((ctype, states[ctype][a.type.name][1].format(a.name)))
            elif a.ob in ab.activities:
                changes.append((ctype, states['activities'][a.type.name][0].format(
                    *[a.title, a.artist] if hasattr(a, 'title') else [a.name])))
        else:
            pass

    if vor.nick == ab.nick:
        pass
    else:
        if not vor.nick:
            changes.append(states['nick'][0].format(ab.nick))
        elif not ab.nick:
            changes.append(states['nick'][1])
        else:
            changes.append(states['nick'][2].format(ab.nick))

    for ctype, msg in changes:
        log.warning(f"{ctype.upper()} - {ab.name} {msg}")


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

    for key, value in states.items():
        before = getattr(vor, key)
        after = getattr(ab, key)
        if before != after:
            if not before:
                msg = value["set"].format(after)
            elif not after:
                msg = value["unset"].format(before)
            else:
                msg = value["update"].format(before, after)

            log.warning(f"{key.upper()} - {member.name} {msg}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


if __name__ == '__main__':
    # TODO: Get TMUX availablity and do stuff accordingly
    try:
        import libtmux

        server = libtmux.Server()
        if os.environ['TMUX']:
            panes = server._list_panes()

            windows = [session.windows for session in server.sessions]
            for pane in panes:
                if pane['pane_current_command'] == "python3" and "Botto" in pane['pane_current_path']:
                    bot.t_session = server.get_by_id(pane["session_id"])
                    bot.t_window = bot.t_session.get_by_id(pane["window_id"])
                    bot.t_pane = bot.t_window.get_by_id(pane["pane_id"])
                    break
                    # # !/usr/bin/env python3
                    #
                    # import libtmux
                    # import os
                    # from pprint import pprint
                    #
                    # server = libtmux.Server()
                    # panes = server._list_panes()
                    # pprint(panes)
                    # for pane in panes:
                    #     if pane['pane_current_command'] == 'python3' and "mine" in pane['pane_current_path']:
                    #         t_session = server.get_by_id(pane["session_id"])
                    #         t_window = t_session.get_by_id(pane["window_id"])
                    #         t_pane = t_window.get_by_id(pane["pane_id"])
                    #         print(type(t_pane))
                    #         print("WE MUXING")
                    #     elif pane['pane_current_command'] == 'java':
                    #         m_session = server.get_by_id(pane["session_id"])
                    #         m_window = t_session.get_by_id(pane["window_id"])
                    #         m_pane = t_window.get_by_id(pane["pane_id"])
                    #         m_pane.send_keys(
                    #             '/tellraw @a [{"text":"[Discord] ","color":"blue"},{"text":"<USERNAME> ","italic":true,"color":"light_purple"},{"text":"Message","italic":true,"color":"white"}]',
                    #             suppress_history=False)

            bot.in_tmux = True
            pass
        else:
            # ...BUT NOT IN TMUX, SOMEHOW GET IN TMUX, AND NAME WINDOW SOMETHING
            pass
    except ImportError:
        # ELSE IF TMUX/LIBTMUX NOT INSTALLED, PASS
        pass
    except KeyError:
        # IF LIBTMUX INSTALLED BUT TMUX NOT RUNNING, PASS
        pass
    credentials = load_credentials()
    botcfg = load_botconfig()
    if not credentials or not botcfg:
        exit(0)
    token = ""
    try:
        token = credentials['token']
    except TypeError:
        log.critical('Auth token is not defined')

    try:
        bot.client_id = credentials['client_id']
    except TypeError:
        log.critical('Client id is not defined')

    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(
                extension, type(e).__name__, e))
            log.error('Failed to load extension {}\n{}: {}'.format(
                extension, type(e).__name__, e))

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
