from discord.ext import commands
import utils.utilities as utilities
import discord

class Misc:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=['who', 'whomst'])
    async def whois(self, ctx):
        """
        whois <@person>
        """
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.author
        roles = user.roles
        rolelist = ""
        for role in roles:
            rolelist += "`" + str(role.name) + "` "
        top_role = user.top_role
        status = user.game
        if status:
            status_type = status.type
            if status_type == 0:
                status_text = "Playing "
            elif status_type == 1:
                status_text = "Streaming "
            elif status_type == 2:
                status_text = "Listening to "
            status_url = status.url
        else:
            status_text = "Idle"
            status = ""
        e = discord.Embed()
        e.set_author(name="Who is " + user.name + "?")
        e.add_field(name="Username", value=user.name + user.discriminator)
        e.add_field(name="Nickname", value=user.nick)
        e.add_field(name="User ID", value=user.id)
        e.add_field(name="Status", value=status_text + str(status))
        e.add_field(name="Roles", value=rolelist)
#         e.add_field(name="", value=str(user.created_at))
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
    bot.add_cog(Misc(bot))
