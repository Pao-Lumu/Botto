from discord.ext import commands
# from utils import checks
import datetime
from discord import Embed
import discord
import asyncio
import json
from pprint import pprint
from collections import Counter
import random

class Comrade:
    """For the glory of the motherland, komrades!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def comrade(self, ctx):
        breeki = ctx.message.clean_content.split(" ")[1:]
        vodka = []
        cyka = False

        comrades = {"I": "We", "i": "we", "I'm": "We are", "i'm": "we are", "I'll": "We will", "i'll": "we will", "I'd": "We'd", "i'd": "we'd", "I've": "We have", "i've": "we have", "my": "our", "mine": "ours", "My": "Our", "Mine": "Ours", "am": "are", "Am": "Are", "Me": "Us", "me": "us"}
        for cheeki in breeki:
            if cheeki in comrades.keys():
                vodka.append("{}".format(comrades[cheeki]))
                cyka = True
            else:
                vodka.append(cheeki)
        if cyka:
            await self.bot.say("""*{}
_**Soviet Anthem Plays**_""".format(" ".join(vodka)))
        else:
            await self.bot.say("Remind Evan to come up with a list of funny, ~~racist~~ Soviet quips to replace this message.")
    

    @commands.command(pass_context=True)
    async def russkipride(self, ctx):
        if self.bot.cooldown_blyat + 360 < datetime.datetime.now().timestamp():
            pass
        else:
            await self.bot.say("Guess who's going to the GUUUULAG! The GUUULAG! The GUUUUUULAG!")
            return
        try:
            if ctx.message.author.voice_channel and not ctx.message.author.is_afk:
                self.bot.cooldown_blyat = datetime.datetime.now().timestamp()
                self.bot.v = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
                player = self.bot.v.create_ffmpeg_player("audio/blyat.ogg")
                player.start()
                await asyncio.sleep(25)
                player.stop()
                await self.bot.v.disconnect()
        except:
            print("Hey lotus why don't you eat a fucking dick")
            await self.bot.say("GO TO GULAG CYKA. DROP AYY DOOBOOYUH PEE RASH B")


def setup(bot):
    bot.add_cog(Comrade(bot))
