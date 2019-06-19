import asyncio
import os
import re
from pprint import pprint

from discord.ext import commands, tasks


class Responder(commands.Cog):
    loop = None

    def __init__(self, bot):
        pprint("HELLO I AM HERE")
        self.bot = bot
        self.loop = bot.loop
        self.lock = asyncio.Lock(loop=bot.loop)
        self.rpc_listen.start()

    @tasks.loop(minutes=1.0, count=1, loop=loop)
    async def rpc_listen(self):
        async with self.lock:
            pass

    @commands.command(aliases=["ul", "u"])
    async def upload(self, ctx, name=""):
        """AAAAAA"""
        try:
            file = ctx.message.attachments[0]
            if name:
                pattern = re.compile(r"\..*(?:\n?)")
                if not re.search(pattern, name):
                    filename = name + re.search(pattern, file.filename)[0]
                else:
                    filename = name
            else:
                filename = file.filename

            if '/' in filename or '\\' in filename:
                await ctx.send("Forward- and back-slashes are not allowed in filenames.", delete_after=10)
                return
            abs_path = os.path.join(os.getcwd(), 'screw_around', filename)
            if os.path.exists(abs_path):
                await ctx.send("File with that filename already exists.", delete_after=10)
                return
            else:
                with open(abs_path, "wb") as new_file:
                    await ctx.message.attachments[0].save(new_file)
        except IndexError:
            await ctx.send("""Please attach exactly one file to a message.
Make sure your file has a file extention as well.""", delete_after=10)
            return
    #
    # @commands.group()
    # async def example_group(self, ctx):
    #     if ctx.subcommand_passed:
    #         pass
    #     else:
    #         pass
    #
    # @example_group.command()
    # async def example_subcommand(self, ctx):
    #     pass


def setup(bot):
    bot.add_cog(Responder(bot))
