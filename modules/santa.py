import asyncio
import json
import os
import pickle
import random
import sqlite3

import discord
from discord.ext import commands


class Santa(commands.Cog):
    """Secret Santa Stuff, and other relevant things idk"""

    def __init__(self, bot):
        self.open_db = None
        self.bot = bot
        self.hohoholy_blessings = asyncio.Lock()
        with open("modules/ogbox.json") as sec:
            self.lookup: dict = json.load(sec)
            self.uplook: dict = {v: k for k, v in self.lookup.items()}
        instant = False if os.path.exists('borderlands_the_pre.sql') else True
        if instant:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()
            cursor.execute("create table santa(user_id, user_name, gifter_id, gifter_name, giftee_id, giftee_name)")
            cursor.execute("create table questions(message_id, question, message_responses)")

    @commands.Cog.listener()
    async def on_add_reaction(self, reaction: discord.Reaction, author: discord.User):
        print(reaction)
        print(author)
        if reaction.message.channel.id == self.bot.meme_channel.id and reaction.emoji == '\N{THUMBS UP SIGN}':
            async with self.hohoholy_blessings:
                try:
                    conn = sqlite3.connect('borderlands_the_pre.sql')
                    cursor = conn.cursor()

                    cursor.execute("select question, message_responses from questions where message_id=?",
                                   (reaction.message.id,))
                    q, responses = cursor.fetchone()
                except ValueError:
                    await self.send_error(author, ReferenceError('Reaction was given to unregistered message.'))
                    raise ReferenceError('Reaction was given to unregistered message.')
                finally:
                    conn.close()
            responses: dict = pickle.loads(responses)
            if str(author.id) not in responses.keys():
                while True:
                    sent = await author.send('Type your question below.', embed=q)

                    def same_channel(msg):
                        return author == msg.author and msg.channel == sent.channel

                    message = await self.bot.wait_for('message', timeout=120.0, check=same_channel)
                    e = discord.Embed(title="Somebody asked...", description=q)
                    for x, y in responses.items():
                        e.add_field(name=self.uplook[x], value=y)
                    e.add_field(name=self.uplook[author.id], value=message.clean_content)
                    preview = await self.send_with_yes_no_reactions(author,
                                                                    message='Does this look correct? (Click \N{THUMBS UP SIGN} for yes and \N{THUMBS DOWN SIGN} for no)',
                                                                    embed=e)
                    try:
                        y_or_n = await self.get_yes_no_reaction(preview)
                        if y_or_n:
                            sent = await author.send('Okay, this message will be sent.')
                            await reaction.message.edit(embed=e)

                            responses[author.id] = message.clean_content
                            rero = pickle.dumps(responses)
                            async with self.hohoholy_blessings:
                                try:
                                    conn = sqlite3.connect('borderlands_the_pre.sql')
                                    cursor = conn.cursor()

                                    cursor.execute("UPDATE questions SET message_responses=? WHERE message_id=?",
                                                   (rero, reaction.message.id,))

                                finally:
                                    conn.commit()
                    except asyncio.TimeoutError as e:
                        print('Timed out.')
                        break
                    except Exception as e:
                        await self.send_error(author, e)

    @commands.command()
    async def secret(self, ctx):
        """Find out who your secret santa is for this year"""
        if ctx.author.id == self.bot.owner_id:
            async with self.hohoholy_blessings:
                conn = sqlite3.connect('borderlands_the_pre.sql')
                cursor = conn.cursor()

                people = list()
                for x, y in self.lookup.items():
                    people.append(x)

                continue_go = True
                while continue_go:
                    random.shuffle(people)
                    for x in range(len(people)):
                        g, r = x % len(people), (x + 1) % len(people)
                        if 'Evan' in (people[g], people[r]) and 'Zach' in (people[g], people[r]):
                            break
                    else:
                        break

                cursor.execute('delete from santa')

                for x, person in enumerate(people):
                    b, g, a = (x - 1) % len(people), x % len(people), (x + 1) % len(people)
                    the_world = (
                        self.lookup[people[b]], people[b], self.lookup[people[g]], people[g], self.lookup[people[a]],
                        people[a])
                    cursor.execute('insert into santa VALUES (?,?,?,?,?,?)', the_world)
                conn.commit()
                conn.close()

            for x, person in enumerate(people):
                discord_id = self.lookup[person]
                gifter = person.capitalize()
                giftee = people[(x + 1) % len(people)].capitalize()
                e = discord.Embed()
                e.title = "{}, you are {}'s secret santa.".format(gifter, giftee)
                e.description = """
Use `>ask` if you'd like to ask them their shirt size, shoe size, favorite color, etc. directly
Use `>respond` if your secret santa `>ask`s you a question via DM and you want to respond.
 
Use `>askall` to ask all participants a question.
To respond to an `>askall` question, click/tap the checkmark under it. You should get a DM from this bot explaining how to respond.

*It's recommended that you go invisible on Discord when you send `>ask` questions, since I can't prevent people from puzzling things out from who's online.*

Recommended price range: <$30, but going slightly over is acceptable.
Secret Santa gifts can be silly or serious.

Please try not to give away who you are to your secret santa, as that ruins the fun of the event.
Misleading your secret santa and giving them a different one is allowed & encouraged.
"""
                # member = self.bot.get_user(141752316188426241)
                member = self.bot.get_user(discord_id)
                print('hi')
                # await member.send(embed=e)
        else:
            async with self.hohoholy_blessings:
                conn = sqlite3.connect('borderlands_the_pre.sql')
                cursor = conn.cursor()
                try:
                    cursor.execute('select * from santa VALUES where user_id=?', (ctx.author.id,))
                    u_id, u_name, _, _, g_id, g_name = cursor.fetchone()
                    await ctx.send("{}, you have been assigned {}'s secret santa.".format(u_name, g_name))
                except ValueError:
                    await ctx.send("You're not a secret santa! If you think this is in error, talk to GrandmaJew.")
                except Exception as e:
                    print(f'{type(e)}: {e}')
                    pass
                conn.close()

    @commands.command()
    async def ask(self, ctx):
        async with self.hohoholy_blessings:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
            u_id, u_name, _, _, g_id, g_name = cursor.fetchone()

        nn = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command)).lstrip()
        if nn:
            member = self.bot.get_user(int(g_id))
            msg = "`>ask` message from your gifter:\n{}".format(nn)
        else:
            await ctx.send("Please add a message.")
        await member.send(content=msg)

    @commands.command()
    async def respond(self, ctx):
        async with self.hohoholy_blessings:
            conn = sqlite3.connect('borderlands_the_pre.sql')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
            u_id, u_name, g_id, g_name, _, _ = cursor.fetchone()

        nn = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command)).lstrip()
        if nn:
            member = self.bot.get_user(int(g_id))
            msg = "`>respond` message from your giftee, {}:\n{}".format(u_name, nn)
            await member.send(content=msg)
        else:
            await ctx.send("Please add a message.")

    @commands.command(aliases=['question', 'poll'])
    async def askall(self, ctx):
        rcvr = ctx.author
        print(ctx.author.dm_channel)
        while True:
            e = discord.Embed(color=discord.Color.green())
            e.set_author(name="Someone asked...")
            question = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command))
            e.description = question
            preview = await self.send_with_yes_no_reactions(rcvr,
                                                            message='This is how your question will look. Are you sure you want to send this message?',
                                                            embed=e)
            try:
                reaction = await self.get_yes_no_reaction(rcvr, message=preview)
                if reaction:
                    await ctx.send('Okay, sending...')
                    mm = await self.bot.meme_channel.send(embed=e)
                    # mm = await self.bot.cfg.santa_channel.send(embed=e)
                    await mm.add_reaction('\N{THUMBS UP SIGN}')

                    async with self.hohoholy_blessings:
                        conn = sqlite3.connect('borderlands_the_pre.sql')
                        cursor = conn.cursor()

                        cursor.execute("insert into questions values (?,?,?)", (mm.id, question, pickle.dumps(dict())))
                        conn.commit()
                    break
                else:
                    await ctx.send('Okay, please type your question again.')
            except asyncio.TimeoutError:
                await ctx.send('Timed out. Please send the `>anonquestion` command again to write a question.')
                break
            except asyncio.CancelledError:
                await ctx.send('Okay, canceled question creation.')
                break
            except Exception as e:
                await self.send_error(ctx, e)

    async def send_with_yes_no_reactions(self, receiver: discord.abc.Messageable, message: str = None,
                                         embed: discord.Embed = None):
        reactions = ('\N{THUMBS UP SIGN}', '\N{THUMBS DOWN SIGN}')

        msg = await receiver.send(message, embed=embed)

        try:
            [await x for x in [msg.add_reaction(reaction) for reaction in reactions]]

        except Exception as e:
            await self.send_error(receiver, e)

        return msg

    async def get_yes_no_reaction(self, rcvr, message: discord.Message = None, timeout=120.0):
        def same_channel(rctn, usr):
            if message:
                print(rcvr.id == usr.id)
                print(rctn.message.channel == rcvr.dm_channel)
                print(rctn.message.id == message.id)
                return rcvr.id == usr.id and rctn.message.channel == rcvr.dm_channel and rctn.message.id == message.id
            else:
                return rcvr.id == usr.id and rctn.message.channel == rcvr.dm_channel

        reaction, author = await self.bot.wait_for('reaction_add', timeout=timeout, check=same_channel)

        if reaction.emoji == '\N{THUMBS UP SIGN}':
            return True
        elif reaction.emoji == '\N{THUMBS DOWN SIGN}':
            return False
        elif reaction.emoji == '\N{CROSS MARK}':
            raise asyncio.CancelledError

    async def send_error(self, rcvr: discord.abc.Messageable, e):
        await rcvr.send(f'Something has gone wrong. Evan has been notified.\nError: {type(e)}: {e}')
        await self.bot.bprint(f'{type(e)}: {e}')
        await self.bot.get_user(self.bot.owner_id).send(f'{type(e)}: {e}')


#
#     @commands.command()
#     async def test(self, rcvr):
#         e = discord.Embed()
#         e.title = "{}, you are {}'s secret santa.".format("Foo", "Bar")
#         e.description = """
# Use `>ask` if you'd like to ask them their shirt size, shoe size, favorite color, etc.
# Use `>respond` if your secret santa `>ask`s you a question via DM and you want to respond.
#
# Use `>askall` to ask all participants a question.
# To respond to an `>askall` question, click/tap the checkmark under it. You should get a DM from this bot explaining how to respond.
#
# It's recommended that you go invisible on Discord when you send `>ask` questions, since I can't prevent people from puzzling things out from who's online.
#
# Recommended price range: <$30, but going slightly over is acceptable.
# Secret Santa gifts can be silly or serious.
# Example: For Xmas 2018, Brandon got an autism shirt, Zach got a unicorn plush, and Aero got a DIY shelf.
#
# Please try not to give away who you are to your secret santa, as that ruins the fun of the event.
# Misleading your secret santa and giving them a different one is allowed & encouraged.
# """
#
#         await rcvr.send(embed=e)
#
#     @commands.command()
#     async def get_reaction(self, rcvr):
#         def check(_, user):
#             return rcvr.author == user
#
#         pp = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
#         print('{}: {} --- {}'.format(type(pp).__name__, pp, pp[0].emoji))
#         await rcvr.send('{}: {}'.format(type(pp).__name__, pp))

# @commands.command()
# async def r(self, receiver):
#     print(receiver.message.clean_content.lstrip(str(receiver.prefix) + str(receiver.command)))
#     print(receiver.message.content.lstrip(str(receiver.prefix) + str(receiver.command)))
#     print('\N{PISTOL}')
#

# Real Numbers
# group = {
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
# group = {
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
