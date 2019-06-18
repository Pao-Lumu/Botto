import asyncio
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

    @commands.command()
    async def upload(self, ctx):
        """AAAAAA"""
        # print(f"\nContext: {dir(ctx)}")
        # print(f"\nMessage: {dir(ctx.message)}")
        for n, a in enumerate(ctx.message.attachments):
            print(f"Attachment {n} ({a.filename}): {dir(a)}")
        else:
            pass
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
