from typing import Iterable, Dict, Tuple
import os
import pathlib
from datetime import datetime
from os import path
from subprocess import PIPE, DEVNULL

import psutil
import toml
from mcstatus import MinecraftServer as mc
from valve.source.a2s import ServerQuerier as src


def get_running() -> psutil.Process:
    try:
        if psutil.WINDOWS:
            print("Windows is not supported.")
            for p in psutil.process_iter(attrs=['connections']):
                for x in p.info['connections']:
                    if x.laddr.port == 22222:
                        return p
                else:
                    continue
            else:
                raise ProcessLookupError('Process not running')
        elif psutil.LINUX:
            ps = psutil.Popen(r"/usr/sbin/ss -tulpn | grep -P :22222 | grep -oP '(?<=pid\=)(\d+)'", shell=True,
                              stdout=PIPE, stderr=DEVNULL)
            pid = ps.stdout.read().decode("utf-8").split('\n')[0]
            if pid:
                proc = psutil.Process(pid=int(pid))
                if proc.username() == psutil.Process().username():
                    return proc
                else:
                    raise ProcessLookupError('Process not running or not accessible by bot.')
    except AttributeError:
        print('Oh no')


def get_game_info() -> Tuple[psutil.Process, Dict]:
    try:
        process = get_running()
        cwd = process.cwd()
    except ProcessLookupError:
        raise ProcessLookupError('Process not running or not accessible by bot.')
    except AttributeError:
        return None, None
    looking_for_gameinfo = True

    while looking_for_gameinfo:
        root, current = path.split(cwd)
        toml_path = path.join(cwd, '.gameinfo.toml')

        if os.path.isfile(toml_path):
            with open(toml_path) as file:
                try:
                    gi = {**{'name': current.title(),
                             'game': '',
                             'folder': cwd,
                             'rcon': '',
                             'executable': process.name(),
                             'command': process.cmdline()},
                          **toml.load(file)}
                except toml.TomlDecodeError as e:
                    print(f"TOML decoding error | {e}")
                    raise toml.TomlDecodeError
            with open(toml_path, "w") as file:
                toml.dump(gi, file)
            return process, gi

        elif "serverfiles" in cwd:
            cwd = root

        elif "serverfiles" not in cwd:
            try:
                # if the TOML file doesn't exist, create it, load defaults, and save
                pathlib.Path(toml_path).touch()
                print(f"created new gameinfo file at {cwd}")
                basic = {'name': current.title(),
                         'game': '',
                         'folder': cwd,
                         'rcon': '',
                         'executable': process.name(),
                         'command': process.cmdline()}
                with open(toml_path, "w+") as file:
                    toml.dump(basic, file)
                return process, basic
            except Exception as e:
                print(f"Exception {type(e)}: {e}")
        else:
            print("Hey... This isn't supposed to happen...")


# def add_to_masterlist(game_info: dict):
#     with open('masterlist.toml') as file:
#         masterlist = toml.load(file)
#     if game_info['folder'] in masterlist.keys():
#         return
#     else:
#         for game_name, game_path in masterlist.items():
#             if [game_info['folder'], game_info['executable']] in game_path and game_name is not game_info['folder']:
#                 masterlist.update(
#                     {game_info['folder']: [game_info['name'], game_info['executable'], game_info['command']]})
#         with open('masterlist.toml', 'w') as file:
#             toml.dump(masterlist, file)


def get_game_version(proc: psutil.Process):
    if proc.is_running() and proc.exe() == 'java':
        server = mc.lookup('localhost:22222')
        info = server.status(retries=2)
        return info.version
    elif proc.is_running() and 'srcds_linux' in proc.exe():
        try:
            with src(('127.0.0.1', 22222)) as server:
                return server.info().get('version')
                # print(server.info())
                # print(server.rules())
                # print(server.ping())
                # print(server.players())
        except:
            return ''
    else:
        return ''
