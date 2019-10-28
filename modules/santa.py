import asyncio
import json
import os
import pickle
import random
import sqlite3

import discord
from discord.ext import commands

from .emoji import Emoji as emoji


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
            cursor.execute("CREATE TABLE santa(user_id, user_name, gifter_id, gifter_name, giftee_id, giftee_name)")
            cursor.execute("CREATE TABLE questions(message_id, question, message_responses)")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        author = self.bot.get_user(reaction.user_id)
        if author.bot:
            return
        if reaction.channel_id == self.bot.meme_channel.id and reaction.emoji.name == emoji.BALLOT_BOX:

            channel = self.bot.get_channel(reaction.channel_id)
            msg_ref = await channel.fetch_message(reaction.message_id)

            async with self.hohoholy_blessings:
                try:
                    conn = sqlite3.connect('borderlands_the_pre.sql')
                    cursor = conn.cursor()

                    cursor.execute("SELECT question, message_responses FROM questions WHERE message_id=?",
                                   (reaction.message_id,))
                    
                    q, responses = cursor.fetchone()
                except TypeError:
                    return
                finally:
                    conn.close()
            responses: dict = pickle.loads(responses)
            while True:
                sent = await author.send(
                    'The question you have been asked is:{}\nType your response below.'.format(q),
                    delete_after=120.0)

                message = await self.bot.wait_for('message', timeout=120.0, check=lambda
                    msg: author == msg.author and msg.channel == sent.channel)
                responses[str(reaction.user_id)] = message.clean_content

                e = discord.Embed(title="Somebody asked...", description=q)
                for x, y in responses.items():
                    e.add_field(name=self.uplook[int(x)], value=y)

                preview = await self.send_with_yes_no_reactions(author,
                                                                message=f'Does this look correct?({emoji.CHECK_MARK} for yes, {emoji.CROSS_MARK} for no)',
                                                                embed=e)
                try:
                    y_or_n = await self.get_yes_no_reaction(author, preview)
                    if y_or_n:
                        await preview.delete()
                        sent = await author.send('Okay, your response will be sent.\nYou may edit it by reacting to the question again.')
                        await msg_ref.edit(embed=e)

                        async with self.hohoholy_blessings:
                            try:
                                conn = sqlite3.connect('borderlands_the_pre.sql')
                                cursor = conn.cursor()

                                cursor.execute("SELECT message_responses FROM questions WHERE message_id=?",
                                               (reaction.message_id,))

                                responses = pickle.loads(cursor.fetchone()[0])
                                responses[str(author.id)] = message.clean_content
                                rero = pickle.dumps(responses)

                                cursor.execute("UPDATE questions SET message_responses=? WHERE message_id=?",
                                               (rero, reaction.message_id,))
                                conn.commit()

                                cursor.execute("SELECT message_responses FROM questions WHERE message_id=?",
                                               (reaction.message_id,))
                                reeeee = cursor.fetchone()

                                e = discord.Embed(title="Somebody asked...", description=q)

                                for x, y in responses.items():
                                    e.add_field(name=self.uplook[int(x)], value=y)
                            except Exception as e:
                                print(type(e))
                                print(e)
                            finally:
                                conn.commit()
                                conn.close()
                                break
                    else:
                        continue
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

                cursor.execute('DELETE FROM santa')

                for x, person in enumerate(people):
                    b, g, a = (x - 1) % len(people), x % len(people), (x + 1) % len(people)
                    the_world = (
                        self.lookup[people[b]], people[b], self.lookup[people[g]], people[g], self.lookup[people[a]],
                        people[a])
                    cursor.execute('INSERT INTO santa VALUES (?,?,?,?,?,?)', the_world)
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
                await member.send(embed=e)
        else:
            async with self.hohoholy_blessings:
                conn = sqlite3.connect('borderlands_the_pre.sql')
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
                    u_id, u_name, _, _, g_id, g_name = cursor.fetchone()
                    await ctx.send("{}, you have been assigned {}'s secret santa.".format(u_name, g_name))
                except TypeError:
                    await ctx.send("You're not a secret santa! If you think this is in error, talk to Evan.")
                except Exception as e:
                    print(f'{type(e)}: {e}')
                    pass
                conn.close()

    @commands.command()
    async def ask(self, ctx):
        async with self.hohoholy_blessings:
            try:
                name = self.uplook[ctx.author.id]
                conn = sqlite3.connect('borderlands_the_pre.sql')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
                u_id, u_name, _, _, g_id, g_name = cursor.fetchone()
            except KeyError:
                await ctx.send("You're not in the secret santa group!")
            except TypeError:
                await ctx.send("Your secret santa has not been assigned!")
            finally:
                conn.close()
        nn = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command)).lstrip()
        if nn:
            member = self.bot.get_user(int(g_id))
            msg = "`>ask` message from your gifter:\n{}".format(nn)
            await member.send(content=msg)
        else:
            await ctx.send("Please add a message.")

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
        while True:
            e = discord.Embed(color=discord.Color.green())
            question = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command))
            e.title = '_*Someone asked:*_\n{}'.format(question)
            preview = await self.send_with_yes_no_reactions(rcvr,
                                                            message='This is how your question will look. Are you sure you want to send this message?',
                                                            embed=e)
            try:
                reaction = await self.get_yes_no_reaction(rcvr, message=preview)
                if reaction:
                    s = await ctx.send('Sending...')
                    mm = await self.bot.meme_channel.send(embed=e)
                    await mm.add_reaction(emoji.BALLOT_BOX)

                    async with self.hohoholy_blessings:
                        conn = sqlite3.connect('borderlands_the_pre.sql')
                        cursor = conn.cursor()

                        cursor.execute("INSERT INTO questions VALUES (?,?,?)", (mm.id, question, pickle.dumps(dict())))
                        conn.commit()
                        conn.close()
                    await s.delete()
                    await ctx.send('Message sent!')
                    break
                else:
                    await ctx.send('Okay, please type your question again.')
                    continue
            except asyncio.TimeoutError:
                await ctx.send('Timed out. Please send the command again')
                break
            except asyncio.CancelledError:
                await preview.delete()
                await ctx.send('Okay, canceled question creation.', delete_after=5)
                break
            except Exception as e:
                await self.send_error(ctx, e)

    async def send_with_yes_no_reactions(self, receiver: discord.abc.Messageable, message: str = None,
                                         embed: discord.Embed = None):
        reactions = (emoji.CHECK_MARK, emoji.CROSS_MARK)

        msg = await receiver.send(message, embed=embed)

        try:
            [await x for x in [msg.add_reaction(reaction) for reaction in reactions]]

        except Exception as e:
            await self.send_error(receiver, e)

        return msg

    async def get_yes_no_reaction(self, rcvr, message: discord.Message = None, timeout=120.0):
        def same_channel(rctn, usr):
            if message:
                return rcvr.id == usr.id and rctn.message.channel == rcvr.dm_channel and rctn.message.id == message.id
            else:
                return rcvr.id == usr.id and rctn.message.channel == rcvr.dm_channel

        reaction, author = await self.bot.wait_for('reaction_add', timeout=timeout, check=same_channel)
        if reaction.emoji == emoji.CHECK_MARK:
            return True
        elif reaction.emoji == emoji.CROSS_MARK:
            return False
        else:
            raise asyncio.CancelledError

    async def send_error(self, rcvr: discord.abc.Messageable, e):
        await rcvr.send(f'Something has gone wrong. Evan has been notified.\nError: {type(e)}: {e}')
        await self.bot.bprint(f'{type(e)}: {e}')
        await self.bot.get_user(self.bot.owner_id).send(f'{type(e)}: {e}')

    @commands.command()
    async def get_reaction(self, rcvr):
        def check(_, user):
            return rcvr.author == user

        pp = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
        print('{}: {} --- {}'.format(type(pp).__name__, pp, pp[0].emoji))
        print(bytes(pp[0].emoji.encode('utf-8')))
        await rcvr.send('{}: {}'.format(type(pp).__name__, pp))

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
