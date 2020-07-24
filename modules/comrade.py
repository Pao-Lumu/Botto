import asyncio
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
    async def on_message(self, message: discord.Message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return
        if 'egg' in message.clean_content.lower():
            egg = [':egg:' for x in range(message.clean_content.lower().count('egg'))]
            await message.channel.send(" ".join(egg))
        if message.attachments:
            for attachment in message.attachments:
                if 'egg' in attachment.filename.lower():
                    egg = [':egg:' for x in range(attachment.filename.lower().count('egg'))]
                    await message.channel.send(" ".join(egg))
        # if message.channel.id == self.bot.meme_channel.id and message.clean_content:
        #     if message.clean_content[0] != '#' and message.clean_content[0] != '>':
        #         await self.auto_comrade_check(message)
        await self.auto_thonk(message)

    # Automatics

    # async def auto_comrade_check(self, msg):
    #     if msg.author.bot:
    #         return
    #     chance = (datetime.now().timestamp() - self.bot.gop_text_cd) / 1200 - .05
    #     if random.random() + chance <= .95:
    #         return
    #     if msg.clean_content:
    #         if msg.clean_content[0] == self.bot.command_prefix:
    #             return
    #     gopnik_text, gopnik_voice = False, False
    #     if self.bot.gop_voice_cd + 3600 < datetime.now().timestamp():
    #         gopnik_voice = True
    #
    #     comrades = {"i": "we",
    #                 "me": "us",
    #                 "am": "are",
    #                 "was": "were",
    #                 "'m": " are",
    #                 "'ll": " will",
    #                 "'d": " would",
    #                 "'ve": " have",
    #                 "my": "our",
    #                 "mine": "ours",
    #                 'myself': 'ourselves'}
    #     ptn = re.compile(r"(?<!\w)(i|me|myself|mine|my|am|was)(\.|\?|!|,|:|;|\"|-|'m|'|\n|\s)", flags=re.IGNORECASE)
    #     try:
    #         raw = re.split(ptn, str(msg.clean_content))
    #     except IndexError:
    #         return
    #     for cheeki, breeki in enumerate(raw):
    #         if breeki.casefold() in comrades.keys():
    #             raw[cheeki] = f"**{comrades[breeki.casefold()].upper()}**"
    #             gopnik_text = True
    #
    #     if gopnik_text:
    #         await msg.channel.send("*" + "".join(raw) + "\n **_Союз нерушимый республик свободных..._**")
    #         self.bot.gop_text_cd = datetime.now().timestamp()
    #         try:
    #             if msg.author.voice and gopnik_voice and not msg.author.voice.afk:
    #                 self.bot.gop_voice_cd = datetime.now().timestamp()
    #
    #                 choir = await msg.author.voice.connect()
    #                 choir.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
    #                 await asyncio.sleep(25)
    #                 choir.stop()
    #
    #                 await choir.disconnect()
    #         except OSError:
    #             self.bot.bprint("Hey lotus why don't you eat a fucking dick ~ Zach 2018")

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
            await ctx.send("*" + "".join(raw) + "\n **_Союз нерушимый республик свободных..._**")

    @helpers.is_human()
    @commands.command()
    async def russkipride(self, ctx):
        if self.bot.gop_voice_cd + 360 < datetime.now().timestamp():
            pass
        else:
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
            self.bot.bprint("Hey lotus why don't you eat a fucking dick ~ Zach 2018")

    @helpers.is_human()
    @commands.command()
    async def rate(self, ctx):
        hsh = hash(ctx.message.clean_content)
        sum_of_hash = 0
        for x in str(abs(hsh)):
            sum_of_hash += int(x)
        egg = sum_of_hash % 6
        donut = sum_of_hash // 12

        await ctx.send(f"""I rate your message...
{" ".join([':egg:' for z in range(0, egg)])} eggs and
{" ".join([':doughnut:' for z in range(0, donut)])} doughnuts""")

    @staticmethod
    async def auto_thonk(msg):
        hmm = re.compile("^[Hh]+[Mm][Mm]+\\.*")
        if re.search(hmm, msg.clean_content):
            await asyncio.sleep(.5)
            await msg.add_reaction('🤔')


def setup(bot):
    bot.add_cog(Comrade(bot))
