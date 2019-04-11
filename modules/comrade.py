import asyncio
# from utils import checks
import datetime
import random

import discord
from discord.ext import commands


class Comrade(commands.Cog):
    """For the glory of the motherland, komrades!"""

    def __init__(self, bot: discord.Client):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 442600877434601475 and message.clean_content:
            if message.clean_content[0] != '#':
                await self.auto_comrade_check(message)

    async def auto_comrade_check(self, msg):
        chance = (datetime.datetime.now().timestamp() - self.bot.cooldown_cyka) / 1200 - .05
        if random.random() + chance <= .95:
            return
        if msg.clean_content:
            if msg.clean_content[0] == '>':
                return
        breeki = msg.clean_content.split(" ")
        cyka, blyat = False, False
        vodka = []
        if self.bot.cooldown_blyat + 3600 < datetime.datetime.now().timestamp():
            blyat = True

        comrades = {"I": "We", "i": "we", "I'm": "We're", "i'm": "we're", "I'll": "We'll", "i'll": "we'll",
                    "I'd": "We'd",
                    "i'd": "we'd", "I've": "We've", "i've": "we've", "my": "our", "mine": "ours", "My": "Our",
                    "Mine": "Ours", "am": "are", "Am": "Are", "Me": "Us", "me": "us"}
        for cheeki in breeki:
            if cheeki in comrades.keys():
                vodka.append("{}".format(comrades[cheeki]))
                cyka = True
            else:
                vodka.append(cheeki)
        if cyka:
            await msg.channel.send("*" + " ".join(vodka) + "\n*Soviet Anthem Plays*")
            self.bot.cooldown_cyka = datetime.datetime.now().timestamp()
        if msg.author.voice_channel and not msg.author.is_afk and cyka and blyat:
            self.bot.cooldown_blyat = datetime.datetime.now().timestamp()
            self.bot.v = await msg.author.voice_channel.connect()
            player = self.bot.v.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
            player.start()
            await asyncio.sleep(25)
            player.stop()
            try:
                await self.bot.v.disconnect()
            except:
                print("Hey lotus why don't you eat a fucking dick")

    @commands.command(pass_context=True)
    async def comrade(self, ctx):
        breeki = ctx.message.clean_content.split(" ")[1:]
        vodka = []
        cyka = False

        comrades = {"I": "We", "i": "we", "I'm": "We are", "i'm": "we are", "I'll": "We will", "i'll": "we will",
                    "I'd": "We'd", "i'd": "we'd", "I've": "We have", "i've": "we have", "my": "our", "mine": "ours",
                    "My": "Our", "Mine": "Ours", "am": "are", "Am": "Are", "Me": "Us", "me": "us"}
        for cheeki in breeki:
            if cheeki in comrades.keys():
                vodka.append("{}".format(comrades[cheeki]))
                cyka = True
            else:
                vodka.append(cheeki)
        if cyka:
            await self.bot.say("*{}\n_**Soviet Anthem Plays**_".format(" ".join(vodka)))
        else:
            await self.bot.say(
                "Remind Evan to come up with a list of funny, ~~racist~~ Soviet quips to replace this message.")

    @commands.command()
    async def russkipride(self, ctx):
        # if self.bot.cooldown_blyat + 360 < datetime.datetime.now().timestamp():
        #     pass
        # else:
        #     await self.bot.say(":musical_note: Guess who's going to the GUUUULAG! The GUUULAG! The GUUUUUULAG! :musical_note:")
        #     return
        try:
            print(dir(ctx))
            print(dir(ctx.author))
            print(dir(ctx.author.voice))
            if ctx.author.voice.channel and not ctx.author.voice.afk:
                print('a')
                self.bot.cooldown_blyat = datetime.datetime.now().timestamp()
                print('a')
                self.bot.v = await ctx.author.voice.channel.connect()
                print('a')
                player = self.bot.v.play(discord.FFmpegPCMAudio("audio/blyat.ogg"))
                print('a')
                await asyncio.sleep(25)
                print('a')
                player.stop()
                print('a')
                await self.bot.v.disconnect()
                print('a')
        except Exception as e:
            print("Hey lotus why don't you eat a fucking dick")
            print(e)
            # await ctx.send("CYKA GO TO GULAG BLYAT. DROP AYY DOOBOOYUH PEE RASH B")
            raise
        except:
            print("FUCK")
        finally:
            for x in self.bot.voice_clients:
                await x.disconnect()

def setup(bot):
    bot.add_cog(Comrade(bot))
