import json
import os
from datetime import datetime
from os import path
from subprocess import PIPE, DEVNULL

import psutil


def get_running():
    current_proc = None
    try:
        if psutil.WINDOWS:
            for p in psutil.process_iter(attrs=['connections']):
                for x in p.info['connections']:
                    if x.laddr.port == 22222:
                        # print(f"Process {p.name()} ({p.pid})")
                        # print(f"    Listening Address: {x.laddr.ip}:{x.laddr.port} ({x.laddr})")
                        current_proc = p
                else:
                    continue
        elif psutil.LINUX:
            ps = psutil.Popen("/usr/sbin/ss -tulpn | grep -P :22222 | grep -oP '(?<=pid\=)(\d+)'", shell=True, stdout=PIPE, stderr=DEVNULL)
            raw = ps.stdout.read().decode("utf-8").rstrip()
            print(raw)
            current_proc = psutil.Process(pid=raw)

    except AttributeError:
        print('Oh no')
    except Exception as e:
        print('ERROR')
        print(e)
        pass
    if current_proc:
        return current_proc
    else:
        return None


def get_game_info():
    process = get_running()
    if not process:
        return None, None
    cwd = process.cwd()
    looking_for_gameinfo = True

    while looking_for_gameinfo:
        root, current = path.split(cwd)
        if os.path.isfile(path.join(cwd, ".gameinfo.json")):
            looking_for_gameinfo = False
            with open(path.join(cwd, ".gameinfo.json")) as file:
                try:
                    gi = json.load(file)
                    return process, gi
                except json.decoder.JSONDecodeError as e:
                    print(f"JSON decoding error | {e}")
                    pass

        elif "serverfiles" in cwd:
            cwd = root
            pass

        elif "serverfiles" not in cwd:
            lr = str(datetime.now().utcnow())
            with open(path.join(cwd, ".gameinfo.json"), "w+") as file:
                basic = {"name": current.title(), "folder": cwd, "last_run": lr, "rcon": "", "version": "",
                         "executable": process.name()}
                json.dump(basic, file)
                return process, basic


def add_to_masterlist(gi):
    with open('masterlist.json') as ml:
        master = json.load(ml)
    if gi["name"] in master.keys():
        pass
    else:
        for name, path in master.items():
            if [gi['folder'], gi['executable']] in path and name is not gi['name']:
                master.update({gi["name"]: [gi['folder'], gi['executable']]})
        with open('masterlist.json', 'w') as ml:
            json.dump(master, ml)

# def fix_mc_rcon_problems(server):
#     fn = os.path.join(server.folder, "server.properties")
#     with open(fn, "r") as p:
#         lines = p.readlines()
#     qp = False
#     rp = False
#     for i, line in enumerate(lines):
#         if "motd" in line:
#             lines[i] = "motd=OGBox Server\n"
#         elif "server-port" in line:
#             lines[i] = "server-port=22222\n"
#         elif "enable-rcon" in line:
#             lines[i] = "enable-rcon=true\n"
#         elif "enable-query" in line:
#             lines[i] = "enable-query=true\n"
#         elif "query.port" in line:
#             lines[i] = "query.port=22222\n"
#             qp = True
#         elif "rcon.port" in line:
#             lines[i] = "rcon.port=22232\n"
#             rp = True
#         else:
#             pass
#
#     if not rp:
#         lines.append("rcon.port=22232\n")
#     if not qp:
#         lines.append("query.port=22222\n")
#
#     with open(fn, 'w') as f:
#         f.writelines(lines)
