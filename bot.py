#!/usr/bin/env python3


import asyncio
import datetime
import logging.handlers
import os
import sys

# noinspection PyPackageRequirements
import discord
import pyfiglet
import toml
# noinspection PyPackageRequirements
from discord.ext import commands

import ogbot_base
from ogbotcmd import OGBotCmd
from utils import helpers

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])

initial_extensions = [
    'modules.admin',
    'modules.santa',
    'modules.music',
    'modules.comrade',
    'modules.server',
    'modules.warframe',
    'modules.game'
]

bot = ogbot_base.OGBot(command_prefix=commands.when_mentioned_or(">"), cog_folder="modules",
                       owner_id=141752316188426241)


@bot.event
async def on_ready():
    bot.loop = asyncio.get_running_loop()
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()
    bot.chat_channel = bot.get_channel(bot.cfg['chat_channel'])
    bot.meme_channel = bot.get_channel(bot.cfg['santa_channel'])
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
        await bot.close()


def load_config() -> dict:
    default = {"credentials": {'token': '', 'client_id': ''},
               "bot_configuration": {'tracked_guild_ids': [], 'chat_channel': 0, 'default_rcon_password': '',
                                     'santa_channel': 0, 'local_ip': '127.0.0.1'}}

    try:
        with open('config.toml') as cfg:
            dd_config = toml.load(cfg)
            for k1, v1 in default.items():
                if k1 not in dd_config.keys():
                    dd_config[k1] = v1
                if isinstance(v1, dict):
                    for k2, v2 in v1.items():
                        if k2 not in dd_config[k1].keys():
                            dd_config[k1][k2] = v2

        with open('config.toml', 'w') as cfg2:
            toml.dump(dd_config, cfg2)
        return dd_config
    except FileNotFoundError:
        log.warning('File "config.toml" not found; Generating...')
        with open('config.toml', 'w+') as cfg3:
            toml.dump(default, cfg3)
        bot.bprint('File "config.toml" not found; Generating...')
        bot.bprint('Please input any relevant information and restart.')
        return {}


# Bot Event Overrides


# @bot.event
# async def on_resumed():
#     bot.bprint('Resumed...')


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
                             'listening': ["is listening to {} by {} on Spotify", "stopped listening to {}"],
                             'watching': ["is watching {}", "stopped watching {}"],
                             'custom': ["set their custom status to `{}`", "cleared their custom status of `{}`",
                                        "changed their custom status from `{}` to `{}`"]}}

    changes = []
    if vor.status == ab.status:
        pass
    else:
        c_type = 'status'
        if ab.status is discord.Status.offline:
            changes.append((c_type, states[c_type][1]))
        elif vor.status is discord.Status.offline:
            changes.append((c_type, states[c_type][0].format(ab.status)))
        else:
            changes.append((c_type, states[c_type][2].format(vor.status, ab.status)))

    if bef == aft:
        pass
    else:
        c_type = 'activities'
        a_states = states[c_type]
        diff = aft.symmetric_difference(bef)

        # I genuinely hate the following patch of code and I want it to die.

        pos = list(filter(lambda x: x.type == discord.ActivityType.custom, diff))
        if len(pos) == 0:
            pass
        else:
            a = discord.ActivityType.custom.name
            if len(pos) == 1:
                if pos[0] in vor.activities:
                    changes.append((c_type, a_states[a][1].format(
                        (f':{pos[0].emoji.name}:' if pos[0].emoji else '') + (' ' if pos[0].name and pos[
                            0].emoji else '') + (pos[0].name if pos[0].name else ''))))
                elif pos[0] in ab.activities:
                    changes.append((c_type, a_states[a][0].format(
                        (f':{pos[0].emoji.name}:' if pos[0].emoji else '') + (' ' if pos[0].name and pos[
                            0].emoji else '') + (pos[0].name if pos[0].name else ''))))

            elif len(pos) == 2:
                af = (f':{pos[0].emoji.name}:' if pos[0].emoji else '') + (' ' if pos[0].name and pos[0].emoji else '')\
                     + (pos[0].name if pos[0].name else '')
                bf = (f':{pos[1].emoji.name}:' if pos[1].emoji else '') + (' ' if pos[1].name and pos[1].emoji else '')\
                     + (pos[1].name if pos[1].name else '')

                if pos[0] in vor.activities:
                    changes.append((c_type, a_states[a][2].format(af, bf)))
                elif pos[0] in ab.activities:
                    changes.append((c_type, a_states[a][2].format(bf, af)))
            else:
                print(pos)
                print(len(pos))

        for a in diff:
            if a.type == discord.ActivityType.custom:
                pass
            elif a.type == discord.ActivityType.listening:
                if a in aft:
                    changes.append((c_type, states['activities'][a.type.name][0].format(
                        *[a.title, a.artist] if hasattr(a, 'title') else [a.name])))
                elif len(diff) % 2 == 1:
                    changes.append((c_type, a_states[a.type.name][1].format(a.name)))

            elif a.ob in vor.activities:
                changes.append((c_type, a_states[a.type.name][1].format(a.name)))
            elif a.ob in ab.activities:
                changes.append((c_type, states['activities'][a.type.name][0].format(
                    *[a.title, a.artist] if hasattr(a, 'title') else [a.name])))
        else:
            pass

    if vor.nick == ab.nick:
        pass
    else:
        c_type = 'nick'
        if not vor.nick:
            changes.append((c_type, states['nick'][0].format(ab.nick)))
        elif not ab.nick:
            changes.append((c_type, states['nick'][1]))
        else:
            changes.append((c_type, states['nick'][2].format(ab.nick)))

    for c_type, msg in changes:
        log.warning(f"{c_type.upper()} - {ab.name} {msg}")


@bot.event
async def on_user_update(vor, ab):
    x = zip((vor.avatar, vor.name, vor.discriminator), (ab.avatar, ab.name, ab.discriminator))
    key = ('avatar', 'name', 'discriminator')

    for y, z in enumerate(x):
        if z[0] == z[1]:
            pass
        else:
            msg = f'{vor.name} changed their {key[y]} from {z[0]} to {z[1]}.'
            log.warning(f"{key[y].upper()} - {msg}")
    pass


@bot.event
async def on_voice_state_update(member, vor, ab):
    if member.guild.id != 442600877434601472:
        return
    states = {"deaf": {"set": "is now server-deafened", "unset": "in no longer server-deafened"},
              "mute": {"set": "is now muted", "unset": "is no longer server-muted"},
              "self_deaf": {"set": "deafened themselves", "unset": "undeafened themselves"},
              "self_mute": {"set": "muted themselves", "unset": "unmuted themselves"},
              "channel": {"set": "joined {}", "update": "moved from {} to {}", "unset": "left {}"}}

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


@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"Command is on cooldown. This is due to API limitations. Try again in {str(error.retry_after)[:5]}s")


if __name__ == '__main__':
    print("starting bot...")
    start = datetime.datetime.now()

    # Setup Logging

    fmt = logging.Formatter('%(asctime)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    sh.setLevel(logging.CRITICAL)

    log = logging.getLogger()
    log.addHandler(sh)
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.CRITICAL)
    discord_logger.addHandler(sh)

    log_path = os.path.join("logs", "ogbot.log")
    if not os.path.exists(log_path):
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "x") as f:
            pass

    fh = logging.handlers.TimedRotatingFileHandler(filename=log_path, when="midnight", encoding='utf-8')
    fh.setFormatter(fmt)
    discord_logger.addHandler(fh)
    log.addHandler(fh)
    # log.warning("LOADED LOGS!")

    # TODO: Get TMUX availablity and do stuff accordingly
    # try:
    #     import libtmux
    #
    #     server = libtmux.Server()
    #     if os.environ['TMUX']:
    #         panes = server._list_panes()
    #
    #         windows = [session.windows for session in server.sessions]
    #         for pane in panes:
    #             if pane['pane_current_command'] == "python3" and "Botto" in pane['pane_current_path']:
    #                 bot.t_session = server.get_by_id(pane["session_id"])
    #                 bot.t_window = bot.t_session.get_by_id(pane["window_id"])
    #                 bot.t_pane = bot.t_window.get_by_id(pane["pane_id"])
    #                 break
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

    #         bot.in_tmux = True
    #         pass
    #     else:
    #         # ...BUT NOT IN TMUX, SOMEHOW GET IN TMUX, AND NAME WINDOW SOMETHING
    #         pass
    # except ImportError:
    #     # ELSE IF TMUX/LIBTMUX NOT INSTALLED, PASS
    #     pass
    # except KeyError:
    #     # IF LIBTMUX INSTALLED BUT TMUX NOT RUNNING, PASS
    #     pass
    config = load_config()
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

    if bot.debug:
        sh.setLevel(logging.DEBUG)
        discord_logger.setLevel(logging.DEBUG)

    bot.log = log
    bot.cfg = config['bot_configuration']
    # game = game.Game(bot)
    try:
        cp1 = datetime.datetime.now() - start
        bot.run(token, start_time=start)
    finally:
        sys.exit(1)
