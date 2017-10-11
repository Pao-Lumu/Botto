from discord.ext import commands
import utilities
from .utils.miki_sql import AccountSQL, GuildSQL
import datetime
import discord

class Birthday:

    def __init__(self, bot):
        self.bot = bot
        self.db = AccountSQL()
        self.gdb = GuildSQL()

    @commands.command(pass_context=True,aliases=['birthdayset', 'setbirthday', 'bds'])
    async def bdayset(self, ctx):
        """
        Use one of the following formats:
        yyyy-mm-dd
        yyyy/mm/dd
        yyyy|mm|dd
        """
        print(dir(ctx))
        print(dir(ctx.message))
        print(dir(ctx.message.channel))
        # print(dir(ctx.message.author))
        # print(ctx.message.author.id)
        # print(dir(ctx.message.type))
        # print(dir(ctx.message.server))
        cmd = await self.extract_cmd_text(ctx)
        year, day, month = cmd[0].replace('|', '-').replace('/', '-').split('-')
        self.db.add(ctx.message.author.id)
        self.db.set_user_birthday(ctx.message.author.id, int(day), int(month), int(year))
        e = await utilities.success_embed('Set birthday for {}!'.format(ctx.message.author.name))
        await self.bot.say(embed=e)

    # @commands.command(pass_context=True, aliases=['bdt', 'birthdaystoday'])
    # async def bdaytoday(self, ctx):
    #     x = datetime.datetime.now().date()
    #     guild = ctx.message.server.id
    #     y,m,d = (x.year, x.month, x.day)
    #     self.db.get_users_with_birthday(d,m,)
    @commands.command(pass_context=True, hidden=True, aliases=['bdaychannelset', 'bdsc'])
    async def bdaysetchannel(self, ctx):
        channel = ''
        guild_id = ctx.message.server.id
        if len(ctx.message.channel_mentions) >= 1:
            channel = ctx.message.channel_mentions[0]
        else:
            channel = ctx.message.channel
        self.gdb.set_guild_birthday_channel(guild_id, channel.id)
        e = await utilities.success_embed('Successfully set birthday announcements channel to {}!'.format(channel.name))
        await self.bot.say(embed=e)

    @commands.command(pass_context=True)
    async def bdayinfo(self, ctx):
        cid = self.gdb.get_guild_birthday_channel(ctx.message.server.id)
        channel = discord.utils.get(ctx.message.server.channels, id=cid)
        y = self.db.get_user_birthday(ctx.message.author.id)
        if y == None:
            y = '\nNot Set'
        await self.bot.say(str(channel)+str(y))
    # @commands.command()
    # async def
    # @commands.command()
    # async def


    async def extract_cmd_text(self, ctx, spaces=-1, chr=' ', index=1):
        if spaces == -1:
            cmd = ctx.message.content.split(chr)[index:]
        else:
            cmd = ctx.message.content.split(chr, spaces)[index:]
        return cmd

def setup(bot):
    bot.add_cog(Birthday(bot))
    print('Loaded module birthday')
