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
        self.bot = bot
        self.hohoholy_blessings = asyncio.Lock()
        with open("modules/ogbox.json") as sec:
            self.lookup: dict = json.load(sec)
            self.uplook: dict = {v: k for k, v in self.lookup.items()}

        instant = False if os.path.exists('borderlands_the_pre.sql') else True
        if instant:
            self.conn = sqlite3.connect('borderlands_the_pre.sql')
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "CREATE TABLE santa(user_id, user_name, gifter_id, gifter_name, giftee_id, giftee_name)")
            self.cursor.execute("CREATE TABLE questions(message_id, question, message_responses)")
            self.conn.commit()
        else:
            self.conn = sqlite3.connect('borderlands_the_pre.sql')
            self.cursor = self.conn.cursor()

    def cog_unload(self):
        self.conn.commit()
        self.conn.close()

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
                    self.cursor.execute("SELECT question, message_responses FROM questions WHERE message_id=?",
                                        (reaction.message_id,))
                    q, responses = self.cursor.fetchone()
                except TypeError:
                    return
            responses: dict = pickle.loads(responses)
            while True:
                sent = await author.send(
                    'The question you have been asked is: {}\nType your response below.'.format(q), delete_after=120.0)

                message = await self.bot.wait_for('message', timeout=120.0, check=lambda
                    msg: author == msg.author and msg.channel == sent.channel)
                responses[str(reaction.user_id)] = message.clean_content

                e = discord.Embed(title="Somebody asked...", description='{}\n\n`VVVV Responses VVVV`'.format(q))
                for x, y in responses.items():
                    e.add_field(name=self.uplook[int(x)], value=y, inline=False)

                preview = await self.send_with_yes_no_reactions(author,
                                                                message=f'Does this look correct?\n({emoji.THUMBS_UP} for yes, {emoji.THUMBS_DOWN} for no)',
                                                                embed=e)
                try:
                    y_or_n = await self.get_yes_no_reaction(author, preview)
                    if y_or_n:
                        await preview.delete()
                        sent = await author.send(
                            'Okay, your response will be sent.\nYou may edit it by reacting to the question again.')
                        await msg_ref.edit(embed=e)

                        async with self.hohoholy_blessings:
                            try:
                                self.cursor.execute("SELECT message_responses FROM questions WHERE message_id=?",
                                                    (reaction.message_id,))

                                responses = pickle.loads(self.cursor.fetchone()[0])
                                responses[str(author.id)] = message.clean_content
                                rero = pickle.dumps(responses)

                                self.cursor.execute("UPDATE questions SET message_responses=? WHERE message_id=?",
                                                    (rero, reaction.message_id,))
                                self.conn.commit()

                                e = discord.Embed(title="Somebody asked...", description=q)
                                for x, y in responses.items():
                                    e.add_field(name=self.uplook[int(x)], value=y, inline=False)

                            except Exception as e:
                                await self.send_error(author, e)
                            finally:
                                self.conn.commit()
                                break
                    else:
                        continue
                except asyncio.TimeoutError:
                    author.send('Timed out. Please try again.')
                    break
                except Exception as e:
                    await self.send_error(author, e)

    @commands.command()
    async def secret(self, ctx):
        """Find out who your secret santa is for this year"""
        if ctx.author.id == self.bot.owner_id:
            async with self.hohoholy_blessings:
                people = list()
                for x, y in self.lookup.items():
                    people.append(x)

                continue_go = True
                while continue_go:
                    random.shuffle(people)

                    used_combos = [
                        # Combos from 2018
                        ('Evan', 'Aero'), ('Aero', 'Zach'), ('Zach', 'Brandon'), ('Brandon', 'Jeromie'),
                        ('Jeromie', 'Steven'), ('Steven', 'David'), ('David', 'Evan'),

                        # Combos from 2019
                        ('Evan', 'Brandon'), ('Brandon', 'Aero'), ('Aero', 'Jeromie'), ('Jeromie', 'Zach'), ('Zach', 'CJ'),
                        ('CJ', 'David'), ('David', 'Steven'), ('Steven', 'Evan')
                    ]
                    banned_combos = [('Evan', 'Zach'), ('CJ', 'Forester'), ('CJ', 'Tim')]

                    continue_go = self.check_for_combos(people, used_combos, banned_combos)

                self.cursor.execute('DELETE FROM santa')

                for x, person in enumerate(people):
                    b, g, a = (x - 1) % len(people), x % len(people), (x + 1) % len(people)
                    the_world = (
                        self.lookup[people[b]], people[b], self.lookup[people[g]], people[g], self.lookup[people[a]],
                        people[a])
                    self.cursor.execute('INSERT INTO santa VALUES (?,?,?,?,?,?)', the_world)
                self.conn.commit()

            for x, person in enumerate(people):
                try:
                    discord_id = self.lookup[person]
                    gifter = person
                    giftee = people[(x + 1) % len(people)]
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
                    member = self.bot.get_user(discord_id) if self.bot.get_user(discord_id) is not None else await self.bot.fetch_user(discord_id)
                    # member = await self.bot.fetch_user(discord_id)
                    # print(f"{gifter}: {giftee}")
                    # print(member)
                    await member.send(embed=e)
                except Exception as e:
                    print(f"{type(e)}: {e}")
        else:
            async with self.hohoholy_blessings:
                try:
                    self.cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
                    u_id, u_name, _, _, g_id, g_name = self.cursor.fetchone()
                    await ctx.send("{}, you have been assigned {}'s secret santa.".format(u_name, g_name))
                except TypeError:
                    await ctx.send("You're not a secret santa! If you think this is in error, talk to Evan.")
                except Exception as e:
                    await self.send_error(ctx, e)
                    pass

    @commands.command()
    async def ask(self, ctx):
        async with self.hohoholy_blessings:
            try:
                # name = self.uplook[ctx.author.id]
                self.cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
                u_id, u_name, _, _, g_id, g_name = self.cursor.fetchone()
            except KeyError:
                await ctx.send("You're not in the secret santa group!")
            except TypeError:
                await ctx.send("Your secret santa has not been assigned!")
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
            self.cursor.execute('SELECT * FROM santa WHERE user_id=?', (ctx.author.id,))
            u_id, u_name, g_id, g_name, _, _ = self.cursor.fetchone()

        nn = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command)).lstrip()
        if nn:
            member = self.bot.get_user(int(g_id))
            msg = "`>respond` message from your giftee, {}:\n{}".format(u_name, nn)
            await member.send(content=msg)
        else:
            await ctx.send("Please add a message.")

    @commands.command(aliases=['poll'])
    async def askall(self, ctx: commands.Context):
        if ctx.channel.type is not discord.ChannelType.private:
            await ctx.send('Please use DMs to set up polls.')
            return
        rcvr = ctx.author
        message = ctx.message
        while True:
            try:
                if not message:
                    await ctx.send('Please type your question.')
                    message = await self.bot.wait_for('message', timeout=120.0, check=lambda
                        msg: rcvr == msg.author and msg.channel == ctx.channel)
                e = discord.Embed(color=discord.Color.green())
                question = message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command))
                for x in ctx.command.aliases:
                    question = question.lstrip(str(x))
                if question == '':
                    message = ''
                    continue
                e.title = '_*Someone asked:*_'
                e.description = '{}\n\n`VVVV Responses VVVV`'.format(question)
                preview = await self.send_with_yes_no_reactions(rcvr,
                                                                message='This is how your question will look. Are you sure you want to send this message?',
                                                                embed=e, extra_reactions=(emoji.CROSS_MARK,))
                try:
                    reaction = await self.get_yes_no_reaction(rcvr, message=preview)
                    if reaction:
                        s = await ctx.send('Sending...')
                        mm = await self.bot.meme_channel.send(embed=e)
                        await mm.add_reaction(emoji.BALLOT_BOX)

                        async with self.hohoholy_blessings:
                            self.cursor.execute("INSERT INTO questions VALUES (?,?,?)",
                                                (mm.id, question, pickle.dumps(dict())))
                            self.conn.commit()
                        await s.delete()
                        await ctx.send('Message sent!')
                        break
                    else:
                        await ctx.send('Okay, restarting...')
                        message = ''
                        continue
                except asyncio.CancelledError:
                    await preview.delete()
                    await ctx.send('Okay, canceled question creation.', delete_after=10)
                    break
            except asyncio.TimeoutError:
                await ctx.send('Timed out. Please send the command again.')
                break
            except Exception as e:
                await self.send_error(ctx, e)

    async def send_with_yes_no_reactions(self, receiver: discord.abc.Messageable, message: str = None,
                                         embed: discord.Embed = None, extra_reactions: tuple = ()):
        reactions = [emoji.THUMBS_UP, emoji.THUMBS_DOWN]

        reactions.extend(extra_reactions)

        msg = await receiver.send(message, embed=embed, delete_after=120.0)

        try:
            for x in reactions:
                await msg.add_reaction(x)

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
        if reaction.emoji == emoji.THUMBS_UP:
            return True
        elif reaction.emoji == emoji.THUMBS_DOWN:
            return False
        else:
            raise asyncio.CancelledError

    async def send_error(self, rcvr: discord.abc.Messageable, e):
        await rcvr.send(f'Something has gone wrong. Evan has been notified.\nError: {type(e)}: {e}')
        await self.bot.bprint(f'{type(e)}: {e}')
        await self.bot.get_user(self.bot.owner_id).send(f'{type(e)}: {e}')

    @staticmethod
    def check_for_combos(check_list, ban_list, superban_list):
        for x, g in enumerate(check_list):
            r = check_list[(x + 1) % len(check_list)]
            if (g, r) in ban_list:
                break
            if (g, r) in superban_list or (r, g) in superban_list:
                break
        else:
            return False
        return True


#     @commands.command()
#     async def get_reaction(self, rcvr):
#         def check(_, user):
#             return rcvr.author == user
#
#         pp = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
#         print('{}: {} --- {}'.format(type(pp).__name__, pp, pp[0].emoji))
#         print(bytes(pp[0].emoji.encode('utf-8')))
#         await rcvr.send('{}: {}'.format(type(pp).__name__, pp))
#
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


def setup(bot):
    bot.add_cog(Santa(bot))
