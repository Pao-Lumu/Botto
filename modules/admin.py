from discord.ext import commands
from utils import checks
from discord import Embed
from utils.botto_sql import GuildSQL
import discord
import asyncio

class Admin:
    """You shouldn't be here..."""

    def __init__(self, bot):
        self.bot = bot
        # self.gdb = GuildSQL(bot.db, bot.cursor)

    @commands.command(hidden=True)
    @checks.is_owner()
    async def reload(self, *, mdl: str):
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
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(hidden=True)
    @checks.is_owner()
    async def prefix(self, *, prefix=None):
        if prefix is None:
            pass
            # TODO: CREATE A USEFUL EMBED FOR THIS
        else:
            self.bot.command_prefix = prefix
            await self.bot.say('Prefix set to: `{}`'.format(prefix))

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def status(self, ctx, *status: str):
        if status:
            await self.bot.change_presence(game=discord.Game(name=" ".join(status)))
            e = await self.bot.say("Success!")
            await asyncio.sleep(5)
            await self.bot.delete_message(e)
            if not ctx.message.channel.is_private:
                await self.bot.delete_message(ctx.message)



    @commands.group("roles")
    @checks.admin_or_perm()
    async def roles(self):
        pass


    # @checks.admin_or_perm()
    # @roles.command(pass_context=True)
    # async def admin(self, ctx, *roll):
    #     if not roll:
    #         return
    #     role = ctx.message.role_mentions[0] if ctx.message.role_mentions else discord.utils.find(lambda m: m.name == " ".join(list(roll)), ctx.message.server.roles)

    #     try:
    #         admin = self.gdb.get_admin_role(ctx.message.server.id)[0]
    #     except:
    #         return

    #     if admin == role.id:
    #         await self.bot.say("Role `{}` is already set as the Admin role.".format(role.name))

    #     self.gdb.set_admin_role(ctx.message.server.id, role_id=role.id)
    #     await self.bot.say("`{}` is now set as the Admin role.".format(role.name))


        # get string or tagged role id
        # if tagged role doesn't exist, error
        # if tagged role is already set as admin, say so and return
        # else set role, say what it was changed from and return
        # role = ctx.message.role_mentions[0]

        # admin = self.gdb.get_admin_role(ctx.guild)

        # return

    # @checks.admin_or_perm()
    # @roles.command(pass_context=True)
    # async def moderator(self, ctx, *roll):
    #     if not roll:
    #         return
    #     role = ctx.message.role_mentions[0] if ctx.message.role_mentions else discord.utils.find(lambda m: m.name == " ".join(list(roll)), ctx.message.server.roles)

    #     try:
    #         mod = self.gdb.get_mod_role(ctx.message.server.id)[0]
    #     except:
    #         return

    #     if mod == role.id:
    #         await self.bot.say("Role `{}` is already set as the Mod role.".format(role.name))

    #     self.gdb.set_mod_role(ctx.message.server.id, role_id=role.id)
    #     await self.bot.say("`{}` is now set as the Mod role.".format(role.name))

    # async def


def setup(bot):
    bot.add_cog(Admin(bot))
