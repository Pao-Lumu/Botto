import asyncio
# from utils import checks
import datetime
import random
import re

import discord
from discord.ext import commands


class Comrade(commands.Cog):
    """For the glory of the motherland, komrades!"""

    def __init__(self, bot: discord.Client):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == self.bot.meme_channel and message.clean_content:
            if message.clean_content[0] != '#':
                await self.auto_comrade_check(message)

    async def auto_comrade_check(self, msg):
        if msg.author.bot:
            return
        chance = (datetime.datetime.now().timestamp() - self.bot.cooldown_cyka) / 1200 - .05
        if random.random() + chance <= .95:
            return
        if msg.clean_content:
            if msg.clean_content[0] == '>':
                return
        cyka, blyat = False, False
        if self.bot.cooldown_blyat + 3600 < datetime.datetime.now().timestamp():
            blyat = True

        comrades = {"i": "we",
                    "me": "us",
                    "am": "are",
                    "was": "were",
                    "'m": " are",
                    "'ll": " will",
                    "'d": " would",
                    "'ve": " have",
                    "my": "our",
                    "mine": "ours",
                    'myself': 'ourselves'}
        ptn = re.compile("""(i|me|myself|mine|my|am|was)(\\.|\\?|!|,|:|;|"|-|'m|'|\n|\\s)""", flags=re.IGNORECASE)
        raw = re.split(ptn, msg.clean_content)

        for cheeki, breeki in enumerate(raw):
            if breeki.casefold() in comrades.keys():
                if breeki.islower():
                    raw[cheeki] = comrades[breeki.casefold()].lower()
                elif breeki.istitle():
                    raw[cheeki] = comrades[breeki.casefold()].capitalize()
                elif breeki.isupper():
                    raw[cheeki] = comrades[breeki.casefold()].upper()
                else:
                    raw[cheeki] = comrades[breeki.casefold()]
                cyka = True

        if cyka:
            await msg.channel.send("*" + "".join(raw) + "\n*Soviet Anthem Plays*")
            self.bot.cooldown_cyka = datetime.datetime.now().timestamp()
        if msg.author.voice and not msg.author.is_afk and cyka and blyat:
            self.bot.cooldown_blyat = datetime.datetime.now().timestamp()
            vc = await msg.author.voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
            await asyncio.sleep(25)
            vc.stop()
            try:
                await vc.disconnect()
            except:
                print("Hey lotus why don't you eat a fucking dick")

    @commands.command(pass_context=True)
    async def comrade(self, ctx):
        cyka = False

        comrades = {"i": "we",
                    "me": "us",
                    "am": "are",
                    "was": "were",
                    "'m": " are",
                    "'ll": " will",
                    "'d": " would",
                    "'ve": " have",
                    "my": "our",
                    "mine": "ours",
                    'myself': 'ourselves'}
        ptn = re.compile("""(i|me|myself|mine|my|am|was)(\\.|\\?|!|,|:|;|"|-|'m|'|\n|\\s)""", flags=re.IGNORECASE)
        raw = re.split(ptn, ctx.message.clean_content)

        for cheeki, breeki in enumerate(raw):
            if breeki.casefold() in comrades.keys():
                if breeki.islower():
                    raw[cheeki] = comrades[breeki.casefold()].lower()
                elif breeki.istitle():
                    raw[cheeki] = comrades[breeki.casefold()].capitalize()
                elif breeki.isupper():
                    raw[cheeki] = comrades[breeki.casefold()].upper()
                else:
                    raw[cheeki] = comrades[breeki.casefold()].capitalize()
                cyka = True

        if cyka:
            await ctx.send("*" + "".join(raw) + "\n*Soviet Anthem Plays*")

    @commands.command()
    async def russkipride(self, ctx):
        if self.bot.cooldown_blyat + 360 < datetime.datetime.now().timestamp():
            pass
        else:
            # await ctx.send(":musical_note: Guess who's going to the GUUUULAG! The GUUULAG! The GUUUUUULAG! :musical_note:")
            return
        try:
            if ctx.author.voice.channel and not ctx.author.voice.afk:
                self.bot.cooldown_blyat = datetime.datetime.now().timestamp()
                vc = await ctx.author.voice.channel.connect()
                vc.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
                await asyncio.sleep(25)
                vc.stop()
                await vc.disconnect()
        except AttributeError as e:
            print(e)
            await ctx.send("GET IN VOICE CHAT BLYAT!")
        except:
            print("Hey lotus why don't you eat a fucking dick")


def setup(bot):
    bot.add_cog(Comrade(bot))
