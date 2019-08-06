#!/usr/bin/env python3.7


import asyncio
import datetime
import logging.handlers
import os
import sys
from collections import defaultdict

# noinspection PyPackageRequirements
import discord
import pyfiglet
import toml
from discord.ext import commands

import game
import ogbot_base
from ogbotcmd import OGBotCmd
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

# initial_extensions = []

initial_extensions = [
    'modules.admin',
    'modules.music',
    'modules.comrade',
    'modules.server'
]

bot = ogbot_base.OGBot(command_prefix=commands.when_mentioned_or(">"), cog_folder="modules",
                       owner_id=141752316188426241)


@bot.event
async def on_ready():
    bot.loop = asyncio.get_running_loop()
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()
    bot.chat_channel = bot.get_channel(bot.cfg['chat_channel'])
    bot.meme_channel = bot.get_channel(bot.cfg['comrade_channel'])
    bot.bprint(f"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
{pyfiglet.figlet_format(bot.user.name, font='epic')}
Username: {bot.user.name}  |  ID: {bot.user.id}
Chat Channel: {bot.chat_channel}  |  Meme Channel: {bot.meme_channel}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~""")

    await asyncio.sleep(3)
    bot.cli = OGBotCmd(bot.loop, bot)
    try:
        await bot.cli.start()
    finally:
        raise KeyboardInterrupt


def load_config() -> dict:
    default = {"credentials": {'token': '', 'client_id': ''},
               "bot_configuration": {'tracked_guild_ids': [], 'chat_channel': 0, 'default_rcon_password': '',
                                     'comrade_channel': 0}}

    try:
        with open('config.toml') as config:
            dd_config = defaultdict(lambda: "", toml.load(config))
            for k, v in default.items():
                if k not in dd_config:
                    dd_config[k] = v
        with open('config.toml', 'w+') as config:
            toml.dump(dd_config, config)
        return dd_config
    except FileNotFoundError:
        log.warning('File "config.toml" not found; Generating...')
        with open('config.toml', 'w+') as config:
            toml.dump(default, config)
        bot.bprint('File "config.toml" not found; Generating...')
        bot.bprint('Please input any relevant information and restart.')
        return {}

# Bot Event Overrides


@bot.event
async def on_resumed():
    bot.bprint('Resumed...')


@bot.event
async def on_member_update(vor, ab):
    if vor.guild.id not in bot.cfg['tracked_guild_ids'] or vor.bot:
        return
    bef = frozenset(map(lambda x: helpers.MiniActivity(x), vor.activities))
    aft = frozenset(map(lambda x: helpers.MiniActivity(x), ab.activities))
    # 0 = set, 1 = unset, 2 = updated
    states = {"status": ["came online ({})", "went offline", "changed status from {} to {}"],
              "nick": ["set their nickname to {}", "deleted their nickname", "changed their nickname to {}"],
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
        ctype = 'nick'
        if not vor.nick:
            changes.append((ctype, states['nick'][0].format(ab.nick)))
        elif not ab.nick:
            changes.append((ctype, states['nick'][1]))
        else:
            changes.append((ctype, states['nick'][2].format(ab.nick)))

    # print(changes)
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
    # credentials = load_credentials()
    # botcfg = load_botconfig()
    config = load_config()
    # if not credentials or not botcfg or not config:
    if not config:
        exit(-1)
    token = ""
    try:
        token = config['credentials']['token']
    except TypeError:
        log.critical('Auth token is not defined')

    try:
        bot.client_id = config['credentials']['client_id']
    except TypeError:
        log.critical('Client id is not defined')

    for extension in initial_extensions:
        try:
            print(extension)
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
    fh.setLevel(logging.ERROR)
    if bot.debug:
        sh.setLevel(logging.DEBUG)
        discord_logger.setLevel(logging.DEBUG)
    discord_logger.addHandler(fh)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    bot.log = log
    # bot.cfg = botcfg
    bot.cfg = config['bot_configuration']
    game = game.Game(bot)
    try:
        bot.run(token)
    finally:
        sys.exit(1)
