# noinspection PyPackageRequirements
import asyncio
import os
from difflib import SequenceMatcher

import discord
from discord.ext import commands

from utils import helpers


class Admin(commands.Cog):
    """You shouldn't be here..."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, mdl: str):
        """Reloads a module."""
        folder = self.bot.cog_folder
        try:
            if mdl.find(".") == -1:
                self.bot.unload_extension("{}.{}".format(folder, mdl))
                self.bot.load_extension("{}.{}".format(folder, mdl))
            else:
                self.bot.unload_extension(mdl)
                self.bot.load_extension(mdl)
        except Exception as e:
            await ctx.send('\N{PISTOL}')
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command()
    async def echo(self, ctx):
        msg = ctx.message.clean_content.lstrip(str(ctx.prefix) + str(ctx.command))
        await ctx.send(content=msg)

    @helpers.is_human()
    @commands.command()
    async def kanye(self, ctx: commands.Context):
        try:
            if ctx.author.voice.channel and not ctx.author.voice.afk:
                vc = await ctx.author.voice.channel.connect()
                if 'cursed' in ctx.message.clean_content:
                    vc.play(discord.FFmpegPCMAudio(source="audio/kanye_singing_cursed.ogg"))
                else:
                    vc.play(discord.FFmpegPCMAudio("audio/kanye_singing.ogg"))
                await asyncio.sleep(30)
                vc.stop()

                await vc.disconnect()
        except AttributeError as e:
            print(e)
            await ctx.send("Not in voice chat.")
        except OSError as e:
            print(e)
            self.bot.bprint("Hey lotus why don't you eat a fucking dick ~ Zach 2018")

    @helpers.is_human()
    @commands.command()
    async def play_meme(self, ctx: commands.Context, *, msg):
        # msg = ctx.message.clean_content
        x = list(map(clean_string, get_music()))
        if not msg:
            e = discord.Embed(title="List of audio clips")
            for fn in x:
                e.add_field(name=fn, value='~~~')
            await ctx.send("List of audio clips:", embed=e)
        else:
            print(msg)
            print(x)
            if msg in x:
                async with helpers.VoiceChatContext(ctx).is_valid_voicechat() as vc:
                    print(vc)
                    vc.play(discord.FFmpegPCMAudio(source=f"audio/{ctx.message.clean_content}.ogg"))
                    await asyncio.sleep(30)
            else:
                e = discord.Embed(title="Audio File Not Found.")
                possible = []
                for fn in x:
                    cleaned = [fn, clean_string(msg)]
                    if msg in fn or get_similarity(*cleaned) > .5 or get_similarity(*cleaned, truncate=True) > .5:
                        possible.append(f"\n~ `{fn}`?")
                if possible:
                    e.description = "Did you mean..." + "".join(possible)
                else:
                    e.description = "Check your spelling."
                await ctx.send(embed=e)

        #     except AttributeError as e:
        #     print(e)
        #     await ctx.send("Not in a voice channel, or unable to access current voice channel.")
        # except OSError as e:
        # print(e)
        # self.bot.bprint("Hey lotus why don't you eat a fucking dick ~ Zach 2018")


def get_similarity(a, b, truncate=False, *args, **kwargs):
    if truncate:
        smol = len(a) if len(a) <= len(b) else len(b)
        return SequenceMatcher(None, a[:smol], b[:smol]).ratio()
    else:
        return SequenceMatcher(None, a, b).ratio()


def clean_string(text: str) -> str:
    # text = ''.join([word for word in text if word not in string.punctuation])
    text = text.rsplit(".", 1)[0].lower()
    return text


def get_music() -> list:
    return os.listdir(path='audio')


def setup(bot):
    bot.add_cog(Admin(bot))
