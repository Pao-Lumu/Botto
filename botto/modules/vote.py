import discord
from discord.ext import commands
from discord.emoji import Emoji

class Vote:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def vote(self, ctx):
        cmd = await self.extract_cmd_text(ctx, 1)
        actual_vote = await self.bot.say(cmd[0])
        for emoji in ('\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}'):
            await self.bot.add_reaction(actual_vote, emoji)


    @commands.command(pass_context=True)
    async def voteopt(self, ctx):
        '''
        voteopt <option1>|<option2>|<option3>|...|<option 9>
        '''
        cmd = await self.extract_cmd_text(ctx, 9, chr='|')
        text = cmd[1].split('|')
        if len(text) <=9:
            actual_vote = await self.bot.say(text)
            for emoji in range(0, len(cmd)):
                num2word = [':one:',':two:',':three:',':four:',':five:',':six:',':seven:',':eight:',':nine:']
                await self.bot.add_reaction(actual_vote, Emoji(name=num2word[emoji]))

    async def extract_cmd_text(self, ctx, spaces: int, chr=' '):
        cmd = ctx.message.content.split(chr, spaces)[1:]
        return cmd

def setup(bot):
    bot.add_cog(Vote(bot))
