import asyncio
import datetime
import os
import sys

import discord

from utils.botto_sql import AccountSQL, GuildSQL
from utils.announcement import Announcement


class BDLoop:

    def __init__(self, bot):
        self.bot = bot
        self.db = AccountSQL(bot.db, bot.cursor)
        self.gdb = GuildSQL(bot.db, bot.cursor)

    async def bday_loop(self):
        guilds = self.gdb.get_all_guild_birthday_channels()
        while True:
            all_channels = []
            if guilds:
                for channel in guilds:
                    bdchannel = discord.Object(id=channel[0])
                    all_channels.append(self._get_bdays(bdchannel))
                await asyncio.gather(*all_channels)
                await asyncio.sleep(60 * 60 * 24)

    async def _get_bdays(self, bdchannel):
        cur_date = datetime.datetime.now().date()
        cur_time = datetime.datetime.now().time()
        year, month, day = (cur_date.year, cur_date.month, cur_date.day)
        bdays = self.db.get_users_with_birthday(day, month)
        time = self.gdb.get_guild_birthday_announcement_time(bdchannel.server.id)[0]
        time_h,time_m = int(time[0:2]), int(time[2:])
        if time_h >
        # IF LAST MESSAGE FROM BOT < 24 HOURS AGO, SPEAK
        # ELSE AWAIT GIVEN TIME
        embed = discord.Embed()
        embed.set_author(name="Birthdays today:")
        if bdays:
            for user in bdays:
                r = discord.utils.get(bdchannel.server.members, id=user[0])
                print(r)
                if r != None:
                    embed.add_field(name=r.name, value='Age: ' +
                                    str(year - int(user[1])))
        else:
            embed.description = "Looks like no one's having a birthday today."
        await Announcement(self.bot, bdchannel).say_list(embed)
