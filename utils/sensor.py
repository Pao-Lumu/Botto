import subprocess
import json
import os
import subprocess
from datetime import datetime
from os import path


# import asyncio

def get_running():
    # ps = subprocess.Popen("/usr/bin/pwdx $(/usr/bin/netstat -tulpen | grep -P :22222 | grep -oP '\d{1,5}(?=\/)')", shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    # TODO REWRITE THIS!!!!
     ps = subprocess.Popen("/usr/bin/pwdx $(/usr/bin/netstat -tulpen | grep -P :22222 | grep -oP '\d{1,5}(?=\/)')", shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
     raw = ps.stdout.read().decode("utf-8").rstrip()
     if raw:
         return raw.split(": ")[1]
     else:
         return None

def init_game_info():
    output = get_running()
    if not output:
        return None
    x = output.split()[0]
    z = True
    while z:
        root, current = path.split(x)
        if os.path.isfile(path.join(x, ".gameinfo.json")):
            z = False
            with open(path.join(x, ".gameinfo.json")) as file:
                try:
                    gi = json.load(file)
                    return gi
                except json.decoder.JSONDecodeError as e:
                        print(f"JSON decoding error | {e}")
                        pass
        elif "serverfiles" in x:
            x = root
            pass
        elif not "serverfiles" in x:
            z = False
            lr = str(datetime.now().timestamp())
            with open(path.join(x, ".gameinfo.json"), "w+") as file:
                basic = {"name": current.title(), "folder": x, "last_run": lr, "rcon": "", "version":""}
                json.dump(basic, file)
                return basic
        else:
            x = root
        pass

def fix_mc_rcon_problems(server):
    fn = os.path.join(server.folder, "server.properties")
    with open(fn, "r") as p:
        l = p.readlines()
    for i, line in enumerate(l):
        if "motd" in line:
            l[i] = "motd=OGBox Server\n"
        if "server-port" in line:
            l[i] = "server-port=22222\n"
        if "enable-rcon" in line:
            l[i] = "enable-rcon=true\n"
        if "enable-query" in line:
            l[i] = "enable-query=true\n"
        if "query.port" in line:
            l[i] = "query.port=22222\n"
        else:
            l.append("query.port=22222\n")
        if "rcon.port" in line:
            l[i] = "rcon.port=22232\n"
        else:
            l.append("rcon.port=22232\n")

    with open(fn, 'w'):
        fn.writelines(l)
