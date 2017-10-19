class BDLoop:

    def __init__(self, bot):
        self.bot = bot
        self.db = AccountSQL(bot.db, bot.cursor)
        self.gdb = GuildSQL(bot.db, bot.cursor)

    async def _bday_loop(self):
        guilds = self.gdb.get_all_guild_birthday_channels()
        while True:
            all_channels = []
            if guilds:
                for channel in guilds:
                    bdchannel = discord.Object(id=channel[0])
                    all_channels.append(self._get_bdays(bdchannel))
                await asyncio.gather(*all_channels)
                await asyncio.sleep(60*60*24)


    async def _get_bdays(self, bdchannel):
        x = datetime.datetime.now().date()
        m, d = (x.month, x.day)
        bdays = self.db.get_users_with_birthday(d, m)
        e = discord.Embed()
        e.set_author(name="Birthdays today:")
        if bdays:
            for user in bdays:
                r = discord.utils.get(bdchannel.server.members, id=user[0])
                if r != None:
                    e.add_field(name=r.name, value='Age: ' + str(y - int(user[1])))
                else:
                    e.description = "Looks like no one's having a birthday today."
        await Announcement(self.bot, bdchannel).say_list(e)

