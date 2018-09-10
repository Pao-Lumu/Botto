from discord.ext import commands
import utils.utilities as utilities
import discord

class ServerControl:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['stats'])
    async def status(self, ctx):
        # Insert server detection code here
        s = False
        e = discord.Embed()
        e.color = color
        if s.online:
            e.set_author(name="Currently Running: ")
            e.add_field(name="Players Online: ", value="")
            e.add_field(name="Uptime", value=user.nick)
            e.add_field(name="", value=user.id)
            e.add_field(name="Status", value=status_text + str(status))
#             e.add_field(name="Roles", value=rolelist)
#             e.add_field(name="", value=str(user.created_at))
        else:
            e.set_author(name="No server is currently running")
        await self.bot.say(embed=e)

    @commands.command(pass_context=True, aliases=['about'])
    async def info(self, ctx):
        """
        Returns information about the bot
        """
        e = discord.Embed()
        e.set_author(name="About {}".format(self.bot.user.name))
        e.add_field(name = "Links", value = "`Server add link:` [click here](https://discordapp.com/api/oauth2/authorize?client_id=370679673904168975&permissions=0&scope=bot)\n`Bug tracker and source code:` [github](https://github.com/TheGrammarJew/Botto)")
        await self.bot.say(embed=e)


def setup(bot):
    bot.add_cog(ServerControl(bot))
