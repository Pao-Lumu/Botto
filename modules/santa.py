import json
import random

import discord
from discord.ext import commands


class Santa:
    """Ho ho ho you're a ho."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def secret(self, ctx):
        """Find out who your secret elf buddy is for this year"""
        with open("modules/secret_santa_people.json") as sec:
            p = json.load(sec)

        s = Santana(p)
        b = s.oye()
        for person, santa in b.items():
            discord_id = int(p[person])
            message = "{}, you have been assigned {} as your secret santa.".format(person.capitalize(),
                                                                                   santa.capitalize())
            member = discord.utils.get(self.bot.get_all_members, id=discord_id)
            await member.send(content=message)

        print(dir(ctx))


class Santana:
    next = "evan"

    def __init__(self, people):
        self.gifter = people.keys()
        self.giftee = people.keys()
        self.gifted = []
        self.people_taken = {}

    def oye(self):
        for i in range(len(self.gifter)):
            santa, secret = self.como(self.next)
            self.giftee.pop(self.giftee.index(secret))
            self.gifted.append(secret)
            self.next = secret
            self.people_taken.update({santa: secret})
        return self.people_taken

    def como(self, name):
        local_gifts = []
        local_gifts.extend(self.giftee)
        if len(self.giftee) == 6:
            return name, 'zach'
        try:
            del local_gifts[local_gifts.index(name)]
        except ValueError:
            pass
        assignment = local_gifts[random.randint(0, len(local_gifts) - 1)]
        if assignment == "evan" and len(self.gifted) is not 6:
            assignment = self.va(local_gifts, ["evan"])
        if name == "evan" and assignment == "zach" or name == "zach" and assignment == "evan":
            assignment = self.va(local_gifts, ["evan", "zach"])

        return name, assignment

    def va(self, local_gifts, exclusions):
        failed = True
        assignment = ""
        while failed:
            assignment = local_gifts[random.randint(0, len(local_gifts) - 1)]
            if assignment not in exclusions:
                failed = False
        return assignment


def setup(bot):
    bot.add_cog(Santa(bot))
