from discord.ext import commands
import aiohttp

from datetime import datetime
import pytz

class Warframe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['barowhen', 'dukey', 'vt'])
    async def baro(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.warframestat.us/pc/voidTrader') as resp:
                info = await resp.json()

        hr_active = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['activation'][:-1]))\
                        .strftime("%A, %B %Y at %I:%M %p %Z")
        hr_expiry = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['expiry'][:-1]))\
                        .strftime("%A, %B %Y at %I:%M %p %Z")

        if info['active']:
            offers = []
            for offer in info['inventory']:
                offers.append(" ~~~ {item} for {ducats} ducats and {credits} credits".format(**offer))

            dukey = """{0} is currently at {1}.
He's currently offering:
{2}
{0} will leave on {3}.
""".format(info['character'], info['location'], "\n".join(offers), hr_expiry)

            await ctx.send(dukey)
        else:
            await ctx.send(f"""{info['character']} will arrive at {info['location']} on {hr_active} and will stay until {hr_expiry}""")

    @commands.group()
    async def example_group(self, ctx):
        if ctx.subcommand_passed:
            pass
        else:
            pass

    @example_group.command()
    async def example_subcommand(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Warframe(bot))
