import asyncio
import random
import re
# from utils import checks
from datetime import datetime

# noinspection PyPackageRequirements,PyPackageRequirements
import discord
# noinspection PyPackageRequirements
from discord.ext import commands

from utils import helpers


class Comrade(commands.Cog):
    """For the glory of the motherland, komrades!"""

    def __init__(self, bot):
        self.bot = bot

    @helpers.is_human()
    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.channel.id == self.bot.meme_channel.id and message.clean_content:
            if message.clean_content[0] != '#' and message.clean_content[0] != '>':
                await self.auto_comrade_check(message)
        await self.auto_thonk(message)

    # Automatics

    async def auto_comrade_check(self, msg):
        if msg.author.bot:
            return
        chance = (datetime.now().timestamp() - self.bot.gop_text_cd) / 1200 - .05
        if random.random() + chance <= .95:
            return
        if msg.clean_content:
            if msg.clean_content[0] == self.bot.command_prefix:
                return
        gopnik_text, gopnik_voice = False, False
        if self.bot.gop_voice_cd + 3600 < datetime.now().timestamp():
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
        ptn = re.compile(r"(?<!\w)(i|me|myself|mine|my|am|was)(\.|\?|!|,|:|;|\"|-|'m|'|\n|\s)", flags=re.IGNORECASE)
        raw = re.split(ptn, str(msg.clean_content).split(" ", 1)[1])

        for cheeki, breeki in enumerate(raw):
            if breeki.casefold() in comrades.keys():
                raw[cheeki] = f"_{comrades[breeki.casefold()].upper()}_"
                gopnik_text = True

        if gopnik_text:
            await msg.channel.send("*" + "".join(raw) + "\n_*Soviet Anthem Plays*_")
            self.bot.gop_text_cd = datetime.now().timestamp()
            try:
                if msg.author.voice and not msg.author.is_afk and gopnik_voice:
                    self.bot.gop_voice_cd = datetime.now().timestamp()

                    choir = await msg.author.voice_channel.connect()
                    choir.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
                    await asyncio.sleep(25)
                    choir.stop()

                    await choir.disconnect()
            except OSError:
                print("Hey lotus why don't you eat a fucking dick")

    # Commands

    @helpers.is_human()
    @commands.command()
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
        ptn = re.compile(r"(?<!\w)(i|me|myself|mine|my|am|was)(\.|\?|!|,|:|;|\"|-|'m|'|\n|\s)", flags=re.IGNORECASE)
        raw = re.split(ptn, str(ctx.message.clean_content).split(" ", 1)[1])

        for cheeki, breeki in enumerate(raw):
            if breeki.casefold() in comrades.keys():
                raw[cheeki] = f"_{comrades[breeki.casefold()].upper()}_"
                gopnik_text = True

        if gopnik_text:
            await ctx.send("*" + "".join(raw) + "\n **_Soviet Anthem Plays_**")

    @helpers.is_human()
    @commands.command()
    async def russkipride(self, ctx):
        if self.bot.gop_voice_cd + 360 < datetime.now().timestamp():
            pass
        else:
            # await ctx.send(":musical_note: Guess who's going to the GUUULAG! The GUULAG! The GUUULAG! :musical_note:")
            return
        try:
            if ctx.author.voice.channel and not ctx.author.voice.afk:
                self.bot.gop_voice_cd = datetime.now().timestamp()

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
