import discord
from random import randrange
from discord.ext import commands


class Reactions:

    dogs = ['https://i.imgur.com/mnUMXnn.jpg','https://i.imgur.com/gM5qDFS.jpg','https://i.imgur.com/hqVWTBL.jpg','https://i.imgur.com/ninvz2s.gifv','https://i.imgur.com/0ydrPTp.gifv','https://i.imgur.com/q8lVC7Y.mp4','https://i.imgur.com/YdlsiIL.jpg','https://i.imgur.com/ToRZyvK.jpg','https://i.imgur.com/NWz24Zl.jpg', 'https://imgur.com/gallery/Uw21RC2','https://i.imgur.com/eDAvzBW.jpg','https://imgur.com/gallery/KQaL5','https://imgur.com/gallery/K8Xcc', 'https://imgur.com/gallery/cMk7o','https://imgur.com/gallery/6kVTD','https://imgur.com/gallery/TxzrZPQ','https://imgur.com/gallery/NusvP9g','https://imgur.com/gallery/xVJ5n']

    cats = ['https://imgur.com/hPAxFc6', 'https://imgur.com/gallery/d8AfKpg','https://imgur.com/gallery/IIyhF','https://imgur.com/gallery/7Zgf2', 'https://imgur.com/gallery/ZhYT2QW','https://i.imgur.com/px2wX4e.jpg','https://i.imgur.com/lJ9qUeT.jpg','https://i.imgur.com/LCbpYxJ.jpg','https://imgur.com/gallery/XHjP2','https://imgur.com/gallery/43RAc']

    foxes = ['https://imgur.com/GcYn5tc', 'https://imgur.com/3MTIPvl', 'https://imgur.com/vOYfgbf', 'https://imgur.com/40RMFx7', 'https://imgur.com/3cC9Bpu', 'https://imgur.com/mOLLT6s', 'https://imgur.com/fi0WDCs', 'https://imgur.com/wGzjiWo', 'https://imgur.com/wkJZZFY', 'https://imgur.com/jS6N8MA', 'https://imgur.com/ZoW7UZw','https://i.imgur.com/4ZmkJuw.gifv']

    others = ['https://imgur.com/8hs1FJy', 'https://imgur.com/NedVAcC', 'https://imgur.com/k6In5Tp', 'https://imgur.com/cGB0Lt4', 'https://imgur.com/VdVsGaM', 'https://imgur.com/ZyyNgrw', 'https://imgur.com/fNzcuxc', 'https://imgur.com/vUuKoHL', 'https://imgur.com/QN1yi2V', 'https://imgur.com/86ajxf5', 'https://imgur.com/Haqa6eM','https://imgur.com/gallery/rMa3CWT','https://imgur.com/gallery/3FxJFLI']

    anything = dogs + cats + foxes + others
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['doggo', 'puppy', 'pup', 'pupper','dogs','pups'])
    async def dog(self):
        pic = self._create_embed(self.dogs)
        await self.bot.say(pic)

    @commands.command(aliases=['kitty','kitten', 'cats'])
    async def cat(self):
        '''
        Put a cute kitty in the channel.
        '''
        pic = self._create_embed(self.cats)
        await self.bot.say(pic)

    @commands.command(aliases=['foxes', 'foxs', 'fax'])
    async def fox(self):
        pic = self._create_embed(self.foxes)
        await self.bot.say(pic)

#     @commands.command()
#     async def baby(self):
#         babies = ['']
#         await self.bot.say(embed=e)a

    @commands.command(aliases=['aww','qt','squee','coot'])
    async def cute(self):
        pic = self._create_embed(self.anything)
        await self.bot.say(pic)

    def _create_embed(self, l):
        return l[randrange(0,len(l),1)]

def setup(bot):
    bot.add_cog(Reactions(bot))
    print("Loaded module reactions")
