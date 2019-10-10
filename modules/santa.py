import json
import random
import sqlite3

import asyncio
from discord.ext import commands


class Santa(commands.Cog):
    """Ho ho ho you're a ho."""

    def __init__(self, bot):
        self.bot = bot
        self.hohoholy_blessings = asyncio.Lock()

    @commands.command()
    async def secret(self, ctx):
        """Find out who your secret elf buddy is for this year"""
        async with self.hohoholy_blessings:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()

            if ctx.author.id == self.bot.owner_id:
                with open("modules/ogbox.json") as sec:
                    lookup = json.load(sec)
                    people = list()
                    for x, y in lookup.items():
                        people.append(x)
                # conn.execute("create table santa(user_id, user_name, gifter_id, gifter_name, giftee_id, giftee_name)")

                continue_go = True
                while continue_go:
                    random.shuffle(people)
                    for x in range(len(people)):
                        g, r = x % len(people), (x + 1) % len(people)
                        if 'evan' in (people[g], people[r]) and 'zach' in (people[g], people[r]):
                            break
                    else:
                        break

                cursor.execute('delete from santa')

                for x, person in enumerate(people):
                    b, g, a = (x - 1) % len(people), x % len(people), (x + 1) % len(people)
                    the_world = (
                        lookup[people[b]], people[b], lookup[people[g]], people[g], lookup[people[a]], people[a])
                    cursor.execute('insert into santa VALUES (?, ?, ?, ?, ?, ?)', the_world)
                    # print(the_world)
                conn.commit()

                for x, person in enumerate(people):
                    discord_id = lookup[person]
                    gifter = person.capitalize()
                    giftee = people[(x + 1) % len(people)].capitalize()
                    message = """
{}, you have been assigned {} as your secret santa.
If you'd like to ask them their shirt size, shoe size, favorite color, ideal date location, a/s/l (okay maybe not those last two...) use `>ask`
If your asks you a question, and you want to respond, use `>respond`

Recommended price limit: idk whatever we decided on lmao

Please try not to give away who you are to your secret santa, as that ruins the fun of the event.
Also, misleading your secret santa into thinking they're getting one gift and giving them a different one is allowed and encouraged.
""".format(gifter, giftee)
                    # member = self.bot.get_user(141752316188426241)
                    member = self.bot.get_user(discord_id)
                    await member.send(content=message)
            else:
                try:
                    # get stuff from sql db
                    pass
                except:
                    # Raise NotASecretSantaError
                    pass

    @commands.command()
    async def ask(self, ctx):
        async with self.hohoholy_blessings:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
            u_id, u_name, _, _, g_id, g_name = cursor.fetchone()

            member = self.bot.get_user(int(g_id))
            msg = "From your gifter:\n {}".format(ctx.message.clean_content.lstrip(
                str(ctx.prefix) + str(ctx.command)))

            await member.send(content=msg)

    @commands.command()
    async def respond(self, ctx):
        async with self.hohoholy_blessings:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
            u_id, u_name, g_id, g_name, _, _ = cursor.fetchone()

            member = self.bot.get_user(int(g_id))
            msg = "From your giftee, {}:\n {}".format(u_name, ctx.message.clean_content.lstrip(
                str(ctx.prefix) + str(ctx.command)))
            await member.send(content=msg)

        # Real Numbers
        # {
        #     "Evan": 141752316188426241,
        #     "Brandon": 146777902501855232,
        #     "Steven": 155794959365046273,
        #     "David": 158704434954764288,
        #     "Zach": 159388909346750465,
        #     "Aero": 239192698836221952,
        #     "Jeromie": 249639501004144640,
        #     "CJ": 530099291478556701
        # }

        # Fake Numbers for testing
        # {
        #     "Evan": 141752316188426241,
        #     "Brandon": 141752316188426241,
        #     "Steven": 141752316188426241,
        #     "David": 141752316188426241,
        #     "Zach": 141752316188426241,
        #     "Aero": 141752316188426241,
        #     "Jeromie": 141752316188426241,
        #     "CJ": 141752316188426241
        # }


def setup(bot):
    bot.add_cog(Santa(bot))
