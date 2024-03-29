import os
from collections import defaultdict
from concurrent import futures

import discord
import mcrcon
import toml
from discord.ext import commands
from mcstatus import MinecraftServer as mc

from utils import utilities
from utils import sensor


class ServerControl(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def masterlist(self, ctx: commands.Context):
        with open('masterlist.toml') as file:
            masterlist = toml.load(file)
            for folder, items in masterlist.items():
                print(f"""~~~~~~~~~~
Game Name: {items['name'].title()}
Folder: {folder}
Items: {items}

""")
        await ctx.send('Sent a debug to the console!')
        pass

    @commands.group(aliases=['mc'])
    async def minecraft(self, ctx: commands.Context):
        if not ctx.subcommand_passed:
            pass

    @commands.is_owner()
    @minecraft.command(aliases=['opt', 'option', 'opts'])
    async def options(self, ctx: commands.Context, *, setting: str = None):
        config = self.parse_config_file()
        try:
            if not setting:
                e = discord.Embed()
                for k, v in config.items():
                    if k == "rcon.password":
                        v = "SET" if v else "NOT SET"
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

                            def unpythonic(mess, bad):
                                if bad.author.id == mess.author.id and bad.channel.id == mess.channel.id:
                                    return True
                                else:
                                    return False

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

        except TypeError:
            pass

    @commands.is_owner()
    @minecraft.command(aliases=['cmd', 'console', 'con'])
    async def command(self, ctx: commands.Context, *, concmd: str):
        try:
            password = self.bot.gameinfo["rcon"] if self.bot.gameinfo["rcon"] else self.bot.cfg["default_rcon_password"]
        except KeyError:
            password = self.bot.cfg["default_rcon_password"]
        try:
            rcon = mcrcon.MCRcon("127.0.0.1", password, 22232)
            rcon.connect()
            x = rcon.command(f'{concmd.lstrip("/")}')
            if x:
                await ctx.send(f'`{x}`')
        except Exception as e:
            await ctx.send(str(e))
        finally:
            rcon.disconnect()

    @commands.is_owner()
    @minecraft.command()
    async def repair(self, ctx: commands.Context):
        mc_defaults = {'motd': 'OGBox Server', 'server-port': '22222', 'enable-rcon': 'true', 'enable-query': 'true'}
        if 'Minecraft' not in str(self.bot.game):
            await ctx.send("Minecraft not running")
        fn = os.path.join(self.bot.game.working_dir, "server.properties")
        with open(fn, "r") as p:
            lines = p.readlines()
        qp, rp = False, False

        for i, line in enumerate(lines):
            for k, v in mc_defaults.items():
                if k in line:
                    lines[i] = f"{k}={v}\n"
            if "query.port" in line:
                lines[i] = "query.port=22222\n"
                qp = True
            elif "rcon.port" in line:
                lines[i] = "rcon.port=22232\n"
                rp = True
            else:
                pass

        if not rp:
            lines.append("rcon.port=22232\n")
            lines.append(f"rcon.password={self.bot.cfg['default_rcon_password']}\n")
        if not qp:
            lines.append("query.port=22222\n")

        with open(fn, 'w') as f:
            f.writelines(lines)

    @minecraft.command()
    async def mods(self, ctx: commands.Context):
        query = mc.lookup("localhost:22222")
        try:
            ree = query.status()
            string = "Mod List:\n\n"
            mods = ree.raw['modinfo']['modList']
            for x in mods:
                if len(string) > 1900:
                    await ctx.send(string)
                    string = ""
                else:
                    string += f"{x['modid']}: {x['version']}\n"
            await ctx.send(string)
        except KeyError:
            await ctx.send("Vanilla")
        except Exception as e:
            print(e)
            print("oh god oh fuck")

    @commands.group()
    async def run(self, ctx: commands.Context):
        # TODO: Find a way to document the executables of each server and use that to create a shutdown/startup thing
        if not ctx.subcommand_passed:
            await ctx.send(embed=await utilities.wip_embed())
            pass

    # HELPER METHODS
    def parse_config_file(self):
        config = defaultdict(lambda: "")
        try:
            p = os.path.join(self.bot.game.working_dir, "server.properties")
            with open(p) as readprop:
                lines = readprop.readlines()
            lines.sort()
            for line in lines:
                if line[0] == "#":
                    continue
                k, v = line.rstrip().split("=")
                config[k] = v if v else ""
            return config
        except TypeError:
            return {}

    def write_config_file(self, config):
        p = os.path.join(self.bot.game.working_dir, "server.properties")

        with open(p, "w") as writeprop:
            for k, v in config.items():
                writeprop.write(f"{k}={v}\n")

    @staticmethod
    def is_forcing(m):
        # I want this to specifically fail safe, which requires checking for an N before a Y
        if "n" in m.clean_content.lower():
            return False
        elif "y" in m.clean_content.lower():
            return True
        else:
            return False

    @commands.is_owner()
    @commands.command()
    async def edit_gameinfo(self, ctx):
        _, gameinfo = sensor.get_game_info()
        e = discord.Embed()
        for k, v in gameinfo.items():
            if isinstance(v, str):
                e.add_field(name=f"{k}: {v}", value="-----------------------------")
        await ctx.send("List of current gameinfo:", embed=e)


def setup(bot):
    bot.add_cog(ServerControl(bot))
