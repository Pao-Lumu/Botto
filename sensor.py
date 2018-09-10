import time
import subprocess
# import asyncio 


ps = subprocess.Popen("/usr/bin/pwdx $(/usr/bin/netstat -tlpen | grep -P :22222 | grep -oP '\d{1,5}(?=\/)')", shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
output = ps.stdout.read().decode("utf-8").rstrip()

games = {"gmod": "GMod", "teeworlds": "Teeworlds", "minecraft": "Minecraft", "tf": "TF2", "css": "CS:Source", "7d2d": "7 Days To Die", "factorio": "Factorio", "terraria": "Terraria", "csgo": "CS:GO", "pyx": "PYX"}
for game in games:
     if output.find(game) != -1:
         print(games[game])
