import json
import os
import pathlib
from datetime import datetime
from os import path
from subprocess import PIPE, DEVNULL

import psutil
import toml


def get_running() -> psutil.Process:
    try:
        if psutil.WINDOWS:
            for p in psutil.process_iter(attrs=['connections']):
                for x in p.info['connections']:
                    if x.laddr.port == 22222:
                        return p
                else:
                    continue
            else:
                raise ProcessLookupError("Process not running")
        elif psutil.LINUX:
            ps = psutil.Popen(r"/usr/sbin/ss -tulpn | grep -P :22222 | grep -oP '(?<=pid\=)(\d+)'", shell=True,
                              stdout=PIPE, stderr=DEVNULL)
            pid = ps.stdout.read().decode("utf-8").split('\n')[0]
            if pid:
                proc = psutil.Process(pid=int(pid))
                if proc.username() == psutil.Process().username():
                    return proc
                else:
                    raise ProcessLookupError("Process not running or not accessable by bot.")

    except AttributeError:
        print('Oh no')


def get_game_info() -> tuple:
    try:
        process = get_running()
    except ProcessLookupError:
        raise ProcessLookupError("Process not currently running.")
    cwd = process.cwd()
    looking_for_gameinfo = True

    while looking_for_gameinfo:
        root, current = path.split(cwd)
        json_path = path.join(cwd, ".gameinfo.json")
        toml_path = path.join(cwd, ".gameinfo.toml")
        # I. If old json file found: Load it, create a TOML file with its data, delete it, and return its data
        if os.path.isfile(json_path):
            # 1. LOAD OLD JSON
            with open(path.join(cwd, ".gameinfo.json")) as file:
                try:
                    gi = json.load(file)
                except json.JSONDecodeError as e:
                    print(f"JSON decoding error | {e}")
                    raise json.JSONDecodeError

            # 2. WRITE TO TOML
            pathlib.Path(path.join(cwd, ".gameinfo.toml")).touch()
            with open(path.join(cwd, ".gameinfo.toml"), "w+") as file:
                toml.dump(gi, file)

            # 3. REMOVE JSON
            os.remove(path.join(cwd, ".gameinfo.json"))
            return process, gi

        # II. If TOML file found: load it, and return the data
        elif os.path.isfile(toml_path):
            with open(path.join(cwd, ".gameinfo.toml")) as file:
                try:
                    gi = toml.load(file)
                except toml.TomlDecodeError as e:
                    print(f"TOML decoding error | {e}")
                    raise toml.TomlDecodeError
            return process, gi

        elif "serverfiles" in cwd:
            cwd = root

        elif "serverfiles" not in cwd:
            # if the TOML file doesn't exist, create it, load defaults, and save
            pathlib.Path(path.join(cwd, ".gameinfo.toml")).touch()
            lr = str(datetime.now().utcnow())
            with open(path.join(cwd, ".gameinfo.toml"), "w+") as file:
                basic = {"name": current.title(), "folder": cwd, "last_run": lr, "rcon": "", "version": "",
                         "executable": process.name()}
                toml.dump(basic, file)
                return process, basic
        else:
            print('Hey... This isn\'t supposed to happen...')


def add_to_masterlist(game_info: dict):
    with open('masterlist.toml') as file:
        masterlist = toml.load(file)
    if game_info["name"] in masterlist.keys():
        return
    else:
        for game_name, game_path in masterlist.items():
            if [game_info['folder'], game_info['executable']] in game_path and game_name is not game_info['name']:
                masterlist.update({game_info["name"]: [game_info['folder'], game_info['executable']]})
        with open('masterlist.toml', 'w') as file:
            toml.dump(masterlist, file)
