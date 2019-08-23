import random
from datetime import datetime

import aiohttp
import discord
import pytz
from discord.ext import commands

import baroaliases


class Warframe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=baroaliases.aliases)
    async def baro(self, ctx):
        """Tells you where and when Baro Ki'Teer comes in Warframe"""

        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.warframestat.us/pc/voidTrader') as resp:
                info = await resp.json()

        hr_active = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['activation'][:-1])) \
            .strftime("%A, %B %d, %Y at %I:%M %p %Z")
        hr_expiry = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['expiry'][:-1])) \
            .strftime("%A, %B %d, %Y at %I:%M %p %Z")

        c = discord.Colour.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if info['active']:
            e = discord.Embed(title="Void Trader Offerings", color=c)
            e.set_footer(text="Baro Ki'Teer")
            for offer in info['inventory']:
                e.add_field(name=offer['item'], value=f"{offer['ducats']} ducats + {offer['credits']} credits")

            dukey = "{0} is currently at {1}, and will leave on {2} {3}.".format(info['character'], info['location'],
                                                                             hr_expiry, info['endString'])

            await ctx.send(dukey, embed=e)
        else:
            e = discord.Embed(title='Void Trader',
                              description=f"""{info['character']} will arrive at {info['location']} on {hr_active} ({info['startString']}) and will stay until {hr_expiry} ({info['endString']})""",
                              color=c)
            await ctx.send(embed=e)

    @commands.command()
    async def nightwave(self, ctx):
        """Lists all the missions for Nightwave at the moment"""

        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.warframestat.us/pc/nightwave') as resp:
                info = await resp.json()
        e = discord.Embed(title="Nightwave Challenges", description="All currently-active Nightwave challenges\n\n")
        e.set_footer(text="Nora Night")

        for challenge in info['activeChallenges']:
            if 'isDaily' in challenge.keys() and challenge['isDaily']:
                e.add_field(name=f" ~ {challenge['title']} (Daily) ({challenge['reputation']} standing)",
                            value=f"   {challenge['desc']}", inline=False)
            elif challenge['isElite']:
                e.add_field(name=f" ~ {challenge['title']} (Weekly Elite) ({challenge['reputation']} standing)",
                            value=f"   {challenge['desc']}", inline=False)
            else:
                e.add_field(name=f" ~ {challenge['title']} (Weekly) ({challenge['reputation']} standing)",
                            value=f"   {challenge['desc']}", inline=False)
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Warframe(bot))
