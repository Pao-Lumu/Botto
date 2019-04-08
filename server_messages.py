import os
from os import path
import re
import socket

import aiofiles
import discord
import mcrcon


class ServerChat:

    def __init__(self, bot):
        self.bot = bot


    async def send_from_server_to_discord():
        await self.bot.wait_until_game_running()
        await asyncio.sleep(1)
        while not bot.is_closed:
            if bot.game == "Minecraft":
                fpath = path.join(bot.gwd, "logs", "latest.log") if path.exists(path.join(bot.gwd, "logs", "latest.log")) else path.join(bot.gwd, "server.log")
                async with aiofiles.open(fpath, loop=bot.loop) as log:
                    await log.seek(0,2)
                    while self.bot.game == "Minecraft":
                        line = ""
                        line = await log.readline()
                        if not line:
                            await asyncio.sleep(.5)
                            continue
                        pattern = re.compile("INFO\]:? (\[.*: .*\].*|\[Server\].*|\<.*\>.*|.* joined the game|.* left the game)")
                        raw_message = re.findall(pattern, str(line))
                        if raw_message:
                            message = raw_message[0]
                            index = message.find('@')
                            if index >= 0:
                                try:
                                    mention = message[index+1:]
                                    length = len(mention)+1
                                    for ind in range(0, length):
                                        member = discord.utils.get(self.bot.chat_channel.server.members, name=mention[:ind])
                                        if member:
                                            message = message.replace("@" + mention[:ind], "<@{}>".format(member.id))
                                            break
                                except Exception as e:
                                    print("ERROR | Server2Discord Exception caught: " + str(e))
                                    pass

                            print("{} | {}".format(self.bot.game, message))
                            await self.bot.send_message(bot.chat_channel, message)
                            continue
            else:
                await asyncio.sleep(15)


    async def send_from_discord_to_server():
        await self.bot.wait_until_game_running()
        await asyncio.sleep(2)
        while not bot.is_closed:
            if bot.game == "Minecraft":
                last_reconnect = datetime.datetime(1, 1, 1)
                rcon = mcrcon.MCRcon("127.0.0.1", "ogboxrcon", 22232)
                try:
                    while bot.game == "Minecraft":
                        msg = await bot.wait_for_message(channel=bot.chat_channel, timeout=5)
                        time_sec = (datetime.datetime.now() - last_reconnect)
                        if time_sec.total_seconds() >= 240 and msg:
                            last_reconnect = datetime.datetime.now()
                            rcon.connect()
                        if msg:
                            if not msg.author.bot:
                                if msg.clean_content:
                                    command = """say §l{}§r: §o{}§r""".format(msg.author.name, msg.clean_content)
                                    if len(command) >= 100:
                                        i = len("say $${}$$: $$$$".format(msg.author.name))
                                        wrapped = textwrap.wrap(msg.clean_content, 100-i)
                                        for i in wrapped:
                                            rcon.command("""say §l{}§r: §o{}§r""".format(msg.author.name, i))
                                    else:
                                        rcon.command("""say §l{}§r: §o{}§r""".format(msg.author.name, msg.clean_content))
                                    print("Discord | <{}>: {}".format(msg.author.name, msg.clean_content))
                                if msg.attachments:
                                    rcon.command("""say §l{}§r: Image {}""".format(msg.author.name, msg.attachments[0]["filename"]))
                                    print("Discord | {}: Image {}".format(msg.author.name, msg.attachments[0]["filename"]))
                        else:
                             pass
                except socket.error as e:
                    rcon.disconnect()
                    print("Socket error: " + e)
                    pass
            else:
                await asyncio.sleep(5)
