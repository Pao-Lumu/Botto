import asyncio
import json
import os
import random
import sqlite3

import discord
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
            instant = True
            if os.path.exists('borderlands_the_pre.sql'):
                instant = False
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()

            if ctx.author.id == self.bot.owner_id:
                # if table does not exist -> create it
                if instant:
                    conn.execute(
                        "create table santa(user_id, user_name, gifter_id, gifter_name, giftee_id, giftee_name)")

                with open("modules/ogbox.json") as sec:
                    lookup = json.load(sec)
                    people = list()
                    for x, y in lookup.items():
                        people.append(x)

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
                conn.commit()

                for x, person in enumerate(people):
                    discord_id = lookup[person]
                    gifter = person.capitalize()
                    giftee = people[(x + 1) % len(people)].capitalize()
                    message = """
{}, you have been assigned {} as your secret santa.
If you'd like to ask them their shirt size, shoe size, favorite color, ideal date location, a/s/l (okay maybe not those last two...) use `>ask`
If your asks you a question, and you want to respond, use `>respond`

Recommended price limit: ~$30

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

    @commands.command(aliases=['question', 'poll'])
    async def anonquestion(self, ctx):
        await ctx.send(
            'Now creating an anonymized question.\nA preview will be displayed in the below message.')
        e = discord.Embed(title='Placeholder')
        preview = await self.send_with_reactions(ctx, embed=e)

        await self.wait_for_reaction(ctx, await self.send_with_reactions(ctx, 'Would you like to add options?'))

        number = 0
        while True:
            number += 1
            await ctx.send(f'Option {number}:')
            val = await self._get_next_message(ctx)
            e.add_field(name=f'Option {number}', value=val.clean_content)
            await preview.edit(embed=e)
            await self.wait_for_reaction(ctx,
                                         await self.send_with_reactions(ctx, 'Would you like to add another option?'))

    async def _get_next_message(self, ctx):
        try:
            msg = await self.bot.wait_for('message', timeout=120.0,
                                          check=lambda message: message.channel == ctx.channel and isinstance(
                                              ctx.channel, discord.DMChannel))
        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))
        return msg

    async def send_with_reactions(self, ctx, message: str = '', embed: discord.Embed = None,
                                  reactions=('\N{THUMBS UP}', '\N{THUMBS DOWN}', '\N{CROSS MARK}')):
        if message and embed:
            msg = await ctx.send(message, embed=embed)
        elif embed:
            msg = await ctx.send(embed=embed)
        else:
            msg = await ctx.send(message)

        for reaction in reactions:
            try:
                await msg.add_reaction(reaction)
            except Exception as e:
                print('{}: {}'.format(type(e).__name__, e))
                # TODO IMPLEMENT THIS
                await self.bot.bprint('{}: {}'.format(type(e).__name__, e))
                # await self.bot('{}: {}'.format(type(e).__name__, e))
                await ctx.send('Something went wrong. Evan has been notified. (Probably)')
                break

        return msg

    async def wait_for_reaction(self, ctx, message: discord.Message, timeout=120.0):
        def same_channel(reaction, user):
            if message:
                return ctx.author == user and reaction.message.channel == ctx.channel and reaction.message == message
            else:
                return ctx.author == user and reaction.message.channel == ctx.channel

        return await self.bot.wait_for('reaction_add', timeout=timeout, check=same_channel)

    # @commands.command()
    # async def get_reaction(self, ctx):
    #     def check(reaction, user):
    #         return ctx.author == user
    #
    #     pp = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
    #     print('{}: {}'.format(type(pp).__name__, pp))
    #     await ctx.send('{}: {}'.format(type(pp).__name__, pp))
    #
    # @commands.command()
    # async def r(self, ctx):
    #     print(ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command)))
    #     print(ctx.message.content.lstrip(str(ctx.prefix) + str(ctx.command)))
    #     print('\N{PISTOL}')
    #

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


# Okay, I guess I'll do any further updates on the bot in here:
# ~ People will be able to ask questions to the entire group anonymously, and everyone will be required to participate.
#  Everyone will also be able to see everyone else's answers.
# ~ Questions to be answered will show up in a channel in this server.
# ~ You will be able to click a reaction button to give a response via DM's (This is for keeping the channel clean, everyone who responds will have their name given.)


def setup(bot):
    bot.add_cog(Santa(bot))
