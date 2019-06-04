from discord.ext import commands
import utils.utilities as utilities
import discord
import os
from collections import defaultdict
from concurrent import futures

class ServerControl(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.group(aliases=['mc'])
    async def minecraft(self, ctx):
        if not ctx.subcommand_passed:
            pass

    @commands.is_owner()
    @minecraft.command(aliases=['opt', 'option', 'opts'])
    async def options(self, ctx, *, setting: str = None):
        config = self.parse_config_file()
        try:
            if not setting:
                e = discord.Embed()
                for k, v in config.items():
                    e.add_field(name=f"{k}: {v}", value="-----------------------------")
                await ctx.send("List of current config options:", embed=e)
            else:
                x = setting.split(" ", maxsplit=1)
                if len(x) == 1:
                    await ctx.send(f"{setting}: {config.get(setting.lower())}")
                else:
                    if x[0].lower() not in config.keys():
                        try:
                            await ctx.send(f"Option `{x[0]}` is not found.\nAdd it anyway? (y/n)", delete_after=15)
                            unpythonic = lambda bad: True if bad.author.id == ctx.message.author.id and bad.channel.id == ctx.message.channel.id else False
                            msg = await self.bot.wait_for('message', check=unpythonic, timeout=10)
                            if "n" in msg.clean_content:
                                await msg.add_reaction('\N{OK HAND SIGN}')
                            elif "y" in msg.clean_content:
                                await ctx.send(f"{x[0]}: `{config.get(x[0])}` --> `{x[1]}`")
                                config[x[0]] = x[1]
                                self.write_config_file(config)
                            else:
                                pass
                        except futures.TimeoutError:
                            pass
                        except NameError:
                            pass
                        except Exception as e:
                            print(e)
                    else:
                        await ctx.send(f"*{x[0]}*: `{config.get(x[0])}` --> `{x[1]}`")
                        config[x[0]] = x[1]
                        self.write_config_file(config)

        except:
            pass

    def parse_config_file(self):
        config = defaultdict(lambda: "")
        try:
            p = os.path.join(self.bot.gwd, "server.properties")
            with open(p) as readprop:
                lines = readprop.readlines()
            lines.sort()
            for line in lines:
                if line[0] == "#":
                    continue
                k, v = line.rstrip().split("=")
                if k == "rcon.password":
                    v = "SET" if v else "NOT SET"
                config[k] = v if v else "NONE"
            return config
        except TypeError:
            return False

    def write_config_file(self, config):
        p = os.path.join(self.bot.gwd, "server.properties")

        with open(p, "w") as writeprop:
            for k, v in config.items():
                print(f"{k}={v}\n")
                writeprop.write(f"{k}={v}\n")

    def is_forcing(self, m):
        # I want this to specifically fail safe, which requires checking for an N before a Y
        if "n" in m.clean_content.lower():
            return True
        elif "y" in m.clean_content.lower():
            return True
        else:
            return False


def setup(bot):
    bot.add_cog(ServerControl(bot))
