from discord.ext import commands


class Admin:
    """You shouldn't be here..."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def reload(self, *, mdl: str):
        """Reloads a module."""
        try:
            self.bot.unload_extension(mdl)
            self.bot.load_extension(mdl)
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')


def setup(bot):
    bot.add_cog(Admin(bot))
