import json
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

    async def fetch(self, session, url):
        async with session.get(url) as response:
            if response.status == 404:
                raise NameError('That is not a valid item. Please check your spelling.')
            else:
                return await response.text()

    async def get_item_orders(self, name):
        async with aiohttp.ClientSession() as session:
            html = await self.fetch(session,
                                    "https://api.warframe.market/v1/items/" + name + "/orders")
            j = json.loads(html)
            return j

    async def get_item_statistics(self, name):
        async with aiohttp.ClientSession() as session:
            html = await self.fetch(session,
                                    "https://api.warframe.market/v1/items/" + name + "/statistics?include=item")
            j = json.loads(html)
            return j

    @commands.command(
        aliases=baroaliases.aliases)
    async def baro(self, ctx):
        """Tells you where and when Baro Ki'Teer is coming on PC Warframe, and what he's selling when he is here."""

        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.warframestat.us/pc/voidTrader') as resp:
                info = await resp.json()

        hr_active = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['activation'][:-1])) \
            .strftime("%A, %B %d, %Y at %I:%M %p %Z")
        hr_expiry = pytz.timezone('America/Chicago').fromutc(datetime.fromisoformat(info['expiry'][:-1])) \
            .strftime("%A, %B %d, %Y at %I:%M %p %Z")

        c = discord.Colour.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if not info['active']:
            e = discord.Embed(title='Void Trader',
                              description=f"""{info['character']} will arrive at {info['location']} on {hr_active} ({info['startString']}) and will stay until {hr_expiry} ({info['endString']})""",
                              color=c)
            await ctx.send(embed=e)
        else:
            e = discord.Embed(title="Void Trader Offerings", color=c)
            e.set_footer(text="Baro Ki'Teer")
            for offer in info['inventory']:
                e.add_field(name=offer['item'], value=f"{offer['ducats']} ducats + {offer['credits']} credits")

            dukey = "{0} is currently at {1}, and will leave on {2} {3}.".format(info['character'], info['location'],
                                                                                 hr_expiry, info['endString'])

            await ctx.send(dukey, embed=e)

    @commands.command()
    async def nightwave(self, ctx):
        """Lists all current Nightwave missions"""

        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.warframestat.us/pc/nightwave') as resp:
                info = await resp.json()

        if info["active"]:
            e = discord.Embed(title="Nightwave Challenges", description="All currently-active Nightwave challenges\n\n")
            e.set_footer(text="Nora Night")

            for challenge in info['activeChallenges']:
                if 'isDaily' in challenge.keys() and challenge['isDaily']:
                    misson_type = "(Daily)"
                elif challenge['isElite']:
                    misson_type = "(Elite Weekly)"
                else:
                    misson_type = "(Weekly)"
                e.add_field(name=f" ~ {challenge['title']} {misson_type} ({challenge['reputation']} standing)",
                            value=f"~~ {challenge['desc']}", inline=False)
            await ctx.send(embed=e)
        else:
            await ctx.send("Nightwave is currently inactive.")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.default)
    async def pricecheck(self, ctx, *, item):
        """Check prices of items on warframe.market"""
        name = str(item).lower().replace(' ', '_')
        x = await self.get_item_statistics(name)
        y = await self.get_item_orders(name)

        for i in x['include']['item']['items_in_set']:
            if x['include']['item']['id'] == i['id']:
                item = i
                break

        two_days = x['payload']['statistics_closed']['48hours']

        td_vol = list()
        td_avg = list()
        sell = list()
        sell_online = list()
        buy = list()
        buy_online = list()

        orders = y['payload']['orders']
        buy.extend(sorted(filter(lambda z: z['order_type'] == "sell", orders), key=lambda y: y['platinum']))
        buy_online.extend(filter(lambda z: z['user']['status'] == "online" or z['user']['status'] == "ingame", buy))
        sell.extend(sorted(filter(lambda z: z['order_type'] == "buy", orders), key=lambda y: y['platinum']))
        sell_online.extend(filter(lambda z: z['user']['status'] == "online" or z['user']['status'] == "ingame", sell))

        for stat in two_days:
            rank = stat.setdefault('mod_rank', None)
            if not rank:
                td_vol.append(stat['volume'])
                td_avg.append(stat['avg_price'])
        vol = sum(td_vol)
        avg = sum(td_avg) / len(td_avg)

        e = discord.Embed()
        e.title = item['en']['item_name']
        e.url = 'https://warframe.market/items/' + item['url_name']
        e.set_author(name='Warframe.market price check')
        e.set_image(url='https://warframe.market/static/assets/' + item['icon'])
        e.set_footer(text='warframe.market',
                     icon_url='https://warframe.market/static/build/assets/frontend/logo.7c3779fb00edc1ee16531ea55bbd5367.png')
        e.description = f"""{vol} {item['en']['item_name']}s sold in the past 48hrs, for {round(avg)}p on average.
        Active Buy Orders start at {int(sell_online[0]['platinum'])}p or less.
        Active Sell Orders start at {int(buy_online[0]['platinum'])}p or more."""

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Warframe(bot))
