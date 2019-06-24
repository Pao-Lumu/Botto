import asyncio
import os

from discord.ext import commands, tasks


class InvalidFileExtensionError(Exception):
    def __init__(self, reason):
        self.reason = reason


class TooManyArgumentsError(Exception):
    def __init__(self, reason):
        self.reason = reason


class Responder(commands.Cog):
    loop = None

    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.lock = asyncio.Lock(loop=bot.loop)
        self.rpc_listen.start()

    @tasks.loop(minutes=1.0, count=1, loop=loop)
    async def rpc_listen(self):
        async with self.lock:
            pass

    @commands.group(aliases=['sb', 'sound'])
    async def soundboard(self, ctx, sound):
        """Literally just for Brandon"""
        if not ctx.subcommand_passed:
            print("")

    @soundboard.command(aliases=["ul", "u"])
    async def upload(self, ctx, name=""):
        """Upload audio to soundboard"""
        valid_extensions = ['ogg', 'mp3', 'wav', 'm4a', 'webm', 'wma']
        filename = ""
        try:
            for file in ctx.message.attachments:
                if name:
                    fn = str(file.filename).split(".", maxsplit=1)
                    gn = str(name).split(".", maxsplit=1)
                    if len(gn) is 1:
                        if fn[1] in valid_extensions:
                            filename = gn[0] + fn[1]
                        else:
                            raise InvalidFileExtensionError("The file extension you gave is not valid.")
                    elif len(gn) is 2:
                        if gn[1] in valid_extensions:
                            filename = name
                    else:
                        raise InvalidFileExtensionError(
                            "If you can read this, you've somehow managed to break existence.")
                else:
                    filename = file.filename

                # Check for malicious filenames
                if '/' in filename or '\\' in filename:
                    await ctx.send("Forward- and back-slashes are not allowed in filenames.", delete_after=10)
                    return

                abs_path = os.path.join(os.getcwd(), 'soundboard', filename)
                if os.path.exists(abs_path):
                    await ctx.send("File with that filename already exists.", delete_after=10)
                    return
                else:
                    with open(abs_path, "wb") as new_file:
                        await ctx.message.attachments[0].save(new_file)
        except IndexError:
            await ctx.send("""E.""", delete_after=10)
            return
        except InvalidFileExtensionError as e:
            await ctx.send(e.reason)
            return
        except TooManyArgumentsError:
            await ctx.send("The filename you gave is formatted incorrectly. Contact the dev for more help.")
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
