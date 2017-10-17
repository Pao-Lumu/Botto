import discord, asyncio
import datetime

class Announcement:

    def __init__(self, bot, channel, time=(1,0,0,0)):
        self.bot = bot
        self.channel = channel
        self.delay = (((time[0]*24)+time[1])*60+time[2])*60+time[3]

    async def say_list(self, content):
        await self.bot.send_message(self.channel, embed=content)

    async def wait_for_time(self, content=""):
        await asyncio.sleep(self.delay)
        await self.bot.send_message(self.channel, content)
