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
                return psutil.Process(pid=int(pid))

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
        if os.path.isfile(path.join(cwd, ".gameinfo.json")):
            # if there's a old json file, find it, delete it, replace it with TOML, and return the data

            # LOAD OLD JSON
            with open(path.join(cwd, ".gameinfo.json")) as file:
                try:
                    gi = json.load(file)
                except json.JSONDecodeError as e:
                    print(f"JSON decoding error | {e}")
                    raise json.JSONDecodeError

            # WRITE TO TOML
            pathlib.Path(path.join(cwd, ".gameinfo.toml")).touch()
            with open(path.join(cwd, ".gameinfo.toml"), "w+") as file:
                toml.dump(gi, file)

            # REMOVE JSON
            os.remove(path.join(cwd, ".gameinfo.json"))

            return process, gi

        elif os.path.isfile(path.join(cwd, ".gameinfo.toml")):
            # if TOML file, load it, and return the data
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


def add_to_masterlist(gi):
    with open('masterlist.toml') as file:
        master = json.load(file)
    if gi["name"] in master.keys():
        pass
    else:
        for name, path in master.items():
            if [gi['folder'], gi['executable']] in path and name is not gi['name']:
                master.update({gi["name"]: [gi['folder'], gi['executable']]})
        with open('masterlist.json', 'w') as file:
            json.dump(master, file)
