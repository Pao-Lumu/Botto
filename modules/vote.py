from discord.ext import commands
import utils.utilities as utilities


class Vote:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['poll', 'yesorno'])
    async def vote(self, ctx):
        """
        <question>
        :param ctx:
        :return:
        """
        cmd = await self.extract_cmd_text(ctx, 1)
        actual_vote = await self.bot.say("Poll: " + str(cmd[0]))
        for emoji in ('\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}'):
            await self.bot.add_reaction(actual_vote, emoji)

    @commands.command(pass_context=True, aliases=['pollopt'])
    async def voteopt(self, ctx):
        """
        <question>|<option1>|<option2>|...|<option 9>
        :param ctx:
        :return:
        """
        cmd = await self.extract_cmd_text(ctx, 9, chr='|', index=0)
        cmd[0] = cmd[0].split(' ', 1)[1]
        if len(cmd) > 10:
            e = await utilities.error_embed("Sorry, I can have up to 9 options on a poll.")
            await self.bot.say(embed=e)
        elif len(cmd) <= 10:
            num2word = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
            text = 'Question: ' + cmd[0] + '\n\n'
            num = 0
            for opt in cmd[1:]:
                text += """{}: {}
""".format(num2word[num], opt)
                num += 1
            actual_vote = await self.bot.say(text)
            for emoji in range(0, len(cmd) - 1):
                await self.bot.add_reaction(actual_vote, num2word[emoji])

    async def extract_cmd_text(self, ctx, spaces: int, chr=' ', index=1):
        cmd = ctx.message.content.split(chr, spaces)[index:]
        return cmd


def setup(bot):
    bot.add_cog(Vote(bot))
