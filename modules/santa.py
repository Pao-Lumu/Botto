from discord.ext import commands
# from utils import checks
from discord import Embed
import discord
import asyncio
import json
from pprint import pprint
from collections import Counter
import random

class Santa:
    """Ho ho ho you're a ho."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    # @checks.owner_only()
    async def secret(self, ctx):
        """Find out who your secret elf buddy is for this year"""
        # with open("modules/oopsallevan.json") as sec:
        with open("modules/secret.json") as sec:
            p = json.load(sec)
        
        s = Santana()
        b = s.lemino()
        for person, santa in b.items():
            discord_id = discord.User(id=p[person])
            message = "{}, you have been assigned {} as your secret santa.".format(person.capitalize(), santa.capitalize())
            await self.bot.send_message(discord_id, content=message)
        
        print(dir(ctx))


class Santana:
    next = "evan"

    def __init__(self):
        pass

    def lemino(self):
        self.gifter = ['evan', 'zach', 'aero', 'jeromie', 'brandon', 'steven', 'david']
        self.giftee = ['evan', 'zach', 'aero', 'jeromie', 'brandon', 'steven', 'david']
        self.gifted = []
        self.people_taken = {}

        for i in range(len(self.gifter)):
            santa, secret = self.verify(self.next)
            self.giftee.pop(self.giftee.index(secret))
            self.gifted.append(secret)
            self.next = secret
            self.people_taken.update({santa: secret})
        return self.people_taken

    def verify(self, name):
        local_gifts = []
        local_gifts.extend(self.giftee)
        if len(self.giftee) == 6:
            return name, 'zach'
        try:
            del local_gifts[local_gifts.index(name)]
        except ValueError:
            pass
        # print("{}: {} vs {}".format(name, len(self.giftee), len(local_gifts)))
        assignment = local_gifts[random.randint(0, len(local_gifts) - 1)]
        if assignment == "evan" and len(self.gifted) is not 6:
            # print("we're getting here")
            assignment = self.retry_on_failure(local_gifts, ["evan"])
        if name == "evan" and assignment == "zach" or name == "zach" and assignment == "evan":
            # print("we're getting here too")
            assignment = self.retry_on_failure(local_gifts, ["evan", "zach"])

        return name, assignment

    def retry_on_failure(self, local_gifts, exclusions):
        failed = True
        while failed:
            # print("we're getting here as well")
            assignment = local_gifts[random.randint(0, len(local_gifts) - 1)]
            if assignment not in exclusions:
                failed = False
        # print("we're getting here also")
        return assignment


    

def setup(bot):
    bot.add_cog(Santa(bot))
