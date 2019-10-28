from discord.ext import commands


class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        pass

    @commands.command()
    async def example_command(self, ctx):
        pass

    @commands.group()
    async def example_group(self, ctx):
        if ctx.subcommand_passed:
            pass
        else:
            pass

    @example_group.command()
    async def example_subcommand(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Example(bot))
