import asyncio

import discord
from discord.ext import commands

from utils import checks


class Admin(commands.Cog):
    """You shouldn't be here..."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @checks.is_owner()
    async def reload(self, *, mdl: str):
        """Reloads a module."""
        folder = self.bot.cog_folder
        try:
            if mdl.find(".") == -1:
                self.bot.unload_extension("{}.{}".format(folder, mdl))
                self.bot.load_extension("{}.{}".format(folder, mdl))
            else:
                self.bot.unload_extension(mdl)
                self.bot.load_extension(mdl)
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def status(self, ctx, *status: str):
        if status:
            await self.bot.change_presence(game=discord.Game(name=" ".join(status)))
            e = await self.bot.say("Success!")
            await asyncio.sleep(5)
            await self.bot.delete_message(e)
            if not ctx.message.channel.is_private:
                await self.bot.delete_message(ctx.message)

    @commands.group("roles")
    @checks.admin_or_perm()
    async def roles(self):
        pass


def setup(bot):
    bot.add_cog(Admin(bot))
