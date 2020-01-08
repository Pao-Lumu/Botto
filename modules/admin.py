# noinspection PyPackageRequirements
import discord
import asyncio
from discord.ext import commands
from utils import helpers


class Admin(commands.Cog):
    """You shouldn't be here..."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, mdl: str):
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
            await ctx.send('\N{PISTOL}')
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command()
    async def echo(self, ctx):
        msg = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command))
        await ctx.send(content=msg)

    @helpers.is_human()
    @commands.command()
    async def kanye(self, ctx: commands.Context):
        try:
            if ctx.author.voice.channel and not ctx.author.voice.afk:
                vc = await ctx.author.voice.channel.connect()
                if 'cursed' in ctx.message.clean_content:
                    vc.play(discord.FFmpegPCMAudio(source="audio/kanye_singing_cursed.ogg"))
                else:
                    vc.play(discord.FFmpegPCMAudio("audio/kanye_singing.ogg"))
                await asyncio.sleep(30)
                vc.stop()

                await vc.disconnect()
        except AttributeError as e:
            print(e)
            await ctx.send("Not in voice chat.")
        except OSError as e:
            print(e)
            self.bot.bprint("Hey lotus why don't you eat a fucking dick ~ Zach 2018")


def setup(bot):
    bot.add_cog(Admin(bot))
