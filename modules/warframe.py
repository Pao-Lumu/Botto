from datetime import datetime

import aiohttp
import discord
import pytz
from discord.ext import commands


class Warframe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['barowhen', 'dukey', 'vt', 'whenthefuckdoesbarokattiercomeyoufuck', 'ducats', 'voidtrader'])
    async def baro(self, ctx):
        """Tells you where and when Baro Ki'Teer comes in Warframe"""

        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.warframestat.us/pc/voidTrader') as resp:
                info = await resp.json()

        hr_active = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['activation'][:-1]))\
                        .strftime("%A, %B %Y at %I:%M %p %Z")
        hr_expiry = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['expiry'][:-1]))\
                        .strftime("%A, %B %Y at %I:%M %p %Z")

        if info['active']:
            e = discord.Embed(title="Baro Ki'Teer Offerings")
            for offer in info['inventory']:
                e.add_field(name=offer['item'], value=f"{offer['ducats']} ducats + {offer['credits']} credits")

            dukey = "{0} is currently at {1}, and will leave on {2}.".format(info['character'], info['location'], hr_expiry)

            await ctx.send(dukey)
        else:
            await ctx.send(f"""{info['character']} will arrive at {info['location']} on {hr_active} and will stay until {hr_expiry}""")


def setup(bot):
    bot.add_cog(Warframe(bot))
