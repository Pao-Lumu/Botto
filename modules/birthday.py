from discord.ext import commands
import utilities
from miki_sql import AccountSQL

class Birthday:

    def __init__(self, bot):
        self.bot = bot
        self.db = AccountSQL()

    @commands.command(pass_context=True)
    async def setbirthday(self, ctx):
        """
        Use one of the following formats:
        yyyy-mm-dd
        yyyy/mm/dd
        yyyy|mm|dd
        :param ctx:
        :return:
        """
        # print(dir(ctx))
        # print(dir(ctx.message))
        print(dir(ctx.message.channel))
        print(dir(ctx.message.author))
        print(ctx.message.author.id)
        print(dir(ctx.message.type))
        print(dir(ctx.message.server))
        cmd = await self.extract_cmd_text(ctx)
        year, day, month = cmd.replace('|', '-').replace('/', '-').split('-')
        self.db.add(ctx.message.author.id)
        self.db.set_user_birthday(ctx.message.author.id, int(day), int(month), int(year))
        e = await utilities.success_embed('Added new birthday for {}!'.format(ctx.message.author.name))
        await self.bot.say(embed=e)

    # @commands.command(aliases=['bdaystoday', 'birthdaystoday'])
    # async def today(self):
    # @commands.command(pass_context=True)
    # async def setbirthdaychannel(self, ctx)
    # @commands.command()
    # async def
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