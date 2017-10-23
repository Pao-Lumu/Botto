from discord.ext import commands
import utils.utilities as utilities
from utils.botto_sql import AccountSQL, GuildSQL
from utils.announcement import Announcement
import datetime
import discord
import asyncio


class Birthday:
    def __init__(self, bot):
        self.bot = bot
        self.db = AccountSQL(bot.db, bot.cursor)
        self.gdb = GuildSQL(bot.db, bot.cursor)



##################
#                #
#    commands    #
#                #
##################


    @commands.command(pass_context=True, aliases=['setbday', 'sbd'])
    async def setbirthday(self, ctx):
        """
        Set your own birthday using the following format: yyyy-mm-dd OR yyyy/mm/dd OR yyyy|mm|dd
        """
        cmd = await self.extract_cmd_text(ctx)
        if cmd:
            year, month, day = cmd[0].replace('|', '-').replace('/', '-').split('-')
            self.db.add(ctx.message.author.id, day, month, year)
            e = await utilities.success_embed(
                'Set birthday for {} to {}-{}-{}!'.format(ctx.message.author.name, year, month, day))
            await self.bot.say(embed=e)
        else:
            e = await utilities.error_embed("Sorry, that's the wrong format. Be sure to use the format: YYYY-MM-DD")

    @commands.command(pass_context=True, aliases=['bdt', 'birthdaytoday', 'bdaystoday', 'bdaytoday'])
    async def birthdaystoday(self, ctx):
        """Displays people who have birthdays today."""
        x = datetime.datetime.now().date()
        guild = ctx.message.server
        y, m, d = (x.year, x.month, x.day)
        bdays = self.db.get_users_with_birthday(d, m)
        e = discord.Embed()
        e.set_author(name="Birthday's today:")
        if bdays:
            for user in bdays:
                r = discord.utils.get(guild.members, id=user[0])
                if r != None:
                    e.add_field(name=r.name, value='Age: ' + str(y - int(user[1])))
        else:
            e.description = "Looks like no one's having a birthday today."
        await self.bot.say(embed=e)

    @commands.command(pass_context=True, hidden=True, aliases=['bdaychannelset', 'bdsc', 'sbdc','setbdaychannel'])
    async def setbirthdaychannel(self, ctx):
        channel = ''
        guild_id = ctx.message.server.id
        if len(ctx.message.channel_mentions) >= 1:
            channel = ctx.message.channel_mentions[0]
        else:
            channel = ctx.message.channel
        self.gdb.set_guild_birthday_channel(guild_id, channel.id)
        e = await utilities.success_embed('Successfully set birthday announcement channel to {}!'.format(channel.name))
        await self.bot.say(embed=e)

    @commands.command(pass_context=True)
    async def birthdayinfo(self, ctx):
        """Shows a server's birthday announcement channel and the user's currently set birthday."""
        cid = self.gdb.get_guild_birthday_channel(ctx.message.server.id)[0]
        channel = discord.utils.get(ctx.message.server.channels, id=cid)
        if len(ctx.message.mentions) >= 1:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.author
        uid = self.db.get_user_birthday(user.id)
        if uid != None:
            birthday = '{}-{}-{}'.format(uid[2], uid[1], uid[0])
        else:
            birthday = 'Not Set'
        e = await utilities.info_embed('Username: {} ({})\nBirthday channel: {}\nUser Birthday: {}'.format(user.nick, user.name, channel.name, birthday))
        await self.bot.say(embed=e)

    @commands.command(pass_context=True)
    async def guildbirthdays(self, ctx):
        guild = ctx.message.server
        bdays = []
        for member in guild.members:
            bdays.append(self.db.get_user_data(member.id))
        e = discord.Embed()
        e.set_author(name="All Birthdays:")
        if bdays:
            for user in bdays:
                if user:
                    r = discord.utils.get(guild.members, id=user[0])
                    if r != None:
                        e.add_field(name=r.name, value='Birthday: ' + datetime.date(int(user[3]),int(user[2]),int(user[1])).strftime('%A, %d %b, %Y'))
        else:
            e.description = "Looks like no one has set their birthday. Use `setbday` to add yours."
        await self.bot.say(embed=e)
        

    async def extract_cmd_text(self, ctx, spaces=-1, chr=' ', index=1):
        if spaces == -1:
            cmd = ctx.message.content.split(chr)[index:]
        else:
            cmd = ctx.message.content.split(chr, spaces)[index:]
        return cmd


def setup(bot):
    bot.add_cog(Birthday(bot))
    print('Loaded module birthday')
