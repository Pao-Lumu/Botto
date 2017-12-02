from discord.ext import commands
from utils import checks

class Admin:
    """You shouldn't be here..."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_owner()
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

    @commands.command()
    @checks.is_owner()
    async def prefix(self, *, prefix: str)
        pass
def setup(bot):
    bot.add_cog(Admin(bot))
