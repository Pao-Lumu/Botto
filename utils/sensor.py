import json
import os
import platform
import subprocess
from datetime import datetime
from os import path


def get_running():
    if platform.system() == 'Windows':
        return None
    else:
        ps = subprocess.Popen(r"/usr/bin/pwdx $(/usr/sbin/ss -tulpn | grep -P :22222 | grep -oP '(?<=pid\=)(\d+)')",
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        raw = ps.stdout.read().decode("utf-8").rstrip()

    if raw:
        return raw.split(": ")[1]
    else:
        return None


def get_game_info():
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
        elif "serverfiles" not in x:
            lr = str(datetime.now().timestamp())
            with open(path.join(x, ".gameinfo.json"), "w+") as file:
                basic = {"name": current.title(), "folder": x, "last_run": lr, "rcon": "", "version": "",
                         "executable": ""}
                json.dump(basic, file)
                return basic


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


def fix_mc_rcon_problems(server):
    fn = os.path.join(server.folder, "server.properties")
    with open(fn, "r") as p:
        lines = p.readlines()
    qp = False
    rp = False
    for i, line in enumerate(lines):
        if "motd" in line:
            lines[i] = "motd=OGBox Server\n"
        elif "server-port" in line:
            lines[i] = "server-port=22222\n"
        elif "enable-rcon" in line:
            lines[i] = "enable-rcon=true\n"
        elif "enable-query" in line:
            lines[i] = "enable-query=true\n"
        elif "query.port" in line:
            lines[i] = "query.port=22222\n"
            qp = True
        elif "rcon.port" in line:
            lines[i] = "rcon.port=22232\n"
            rp = True
        else:
            pass

    if not rp:
        lines.append("rcon.port=22232\n")
    if not qp:
        lines.append("query.port=22222\n")

    with open(fn, 'w') as f:
        f.writelines(lines)
