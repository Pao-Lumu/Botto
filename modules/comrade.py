import asyncio
# from utils import checks
import datetime
import random
import re

# noinspection PyPackageRequirements,PyPackageRequirements
import discord
# noinspection PyPackageRequirements
from discord.ext import commands

import ogbot_base


class Comrade(commands.Cog):
    """For the glory of the motherland, komrades!"""

    def __init__(self, bot: ogbot_base.OGBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if not message.author.bot:
            if message.channel.id == self.bot.meme_channel.id and message.clean_content:
                if message.clean_content[0] != '#':
                    await self.auto_comrade_check(message)
            await self.auto_thonk(message)

    async def auto_comrade_check(self, msg):
        if msg.author.bot:
            return
        chance = (datetime.datetime.now().timestamp() - self.bot.gop_text_cd) / 1200 - .05
        if random.random() + chance <= .95:
            return
        if msg.clean_content:
            if msg.clean_content[0] == '>':
                return
        gopnik_text, gopnik_voice = False, False
        if self.bot.gop_voice_cd + 3600 < datetime.datetime.now().timestamp():
            gopnik_voice = True

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
        ptn = re.compile("""(?<!\\w)(i|me|myself|mine|my|am|was)(\\.|\\?|!|,|:|;|"|-|'m|'|\n|\\s)""",
                         flags=re.IGNORECASE)
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
                gopnik_text = True

        if gopnik_text:
            await msg.channel.send("*" + "".join(raw) + "\n*Soviet Anthem Plays*")
            self.bot.gop_text_cd = datetime.datetime.now().timestamp()
        if msg.author.voice and not msg.author.is_afk and gopnik_text and gopnik_voice:
            self.bot.gop_voice_cd = datetime.datetime.now().timestamp()
            vc = await msg.author.voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
            await asyncio.sleep(25)
            vc.stop()
            try:
                await vc.disconnect()
            except OSError:
                print("Hey lotus why don't you eat a fucking dick")

    @commands.command(pass_context=True)
    async def comrade(self, ctx):
        gopnik_text = False

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
        ptn = re.compile("""(?<!\\w)(i|me|myself|mine|my|am|was)(\\.|\\?|!|,|:|;|"|-|'m|'|\n|\\s)""",
                         flags=re.IGNORECASE)
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
                gopnik_text = True

        if gopnik_text:
            await ctx.send("*" + "".join(raw) + "\n*Soviet Anthem Plays*")

    @commands.command()
    async def russkipride(self, ctx):
        if self.bot.gop_voice_cd + 360 < datetime.datetime.now().timestamp():
            pass
        else:
            # await ctx.send(":musical_note: Guess who's going to the GUUULAG! The GUULAG! The GUUULAG! :musical_note:")
            return
        try:
            if ctx.author.voice.channel and not ctx.author.voice.afk:
                self.bot.gop_voice_cd = datetime.datetime.now().timestamp()
                vc = await ctx.author.voice.channel.connect()
                vc.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
                await asyncio.sleep(25)
                vc.stop()
                await vc.disconnect()
        except AttributeError as e:
            print(e)
            await ctx.send("GET IN VOICE CHAT BLYAT!")
        except OSError:
            print("Hey lotus why don't you eat a fucking dick")

    @staticmethod
    async def auto_thonk(msg):
        hmm = re.compile("^[Hh]+[Mm][Mm]+\\.*")
        if re.search(hmm, msg.clean_content):
            await asyncio.sleep(.5)
            await msg.add_reaction('🤔')


def setup(bot):
    bot.add_cog(Comrade(bot))
