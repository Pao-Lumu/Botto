import asyncio
import datetime
import inspect
import platform

import colorama
from colorama import Fore
from discord.ext import commands

from utils import checks


class Botto(commands.Bot):
    def __init__(self, *args, **kwargs):
        colorama.init()
        self.loop = kwargs.pop('loop', asyncio.get_event_loop())
        self.cog_folder = kwargs.pop('cog_folder')
        self.game = ""
        self.cooldown_cyka = 0
        self.cooldown_blyat = 0
        if platform.system() == "Linux":
            asyncio.get_child_watcher().attach_loop(self.loop)
        command_prefix = kwargs.pop('command_prefix', commands.when_mentioned_or('.'))
        # self.debug = True
        self.debug = False

        self._game_running = asyncio.Event(loop=self.loop)
        self._game_stopped = asyncio.Event(loop=self.loop)

        super().__init__(command_prefix=command_prefix, *args, **kwargs)

    async def wait_until_ready(self, delay=0):
        if self.debug:
            self.bprint("Waiting for the bot to start...")
        await super().wait_until_ready()
        if delay:
            await asyncio.sleep(delay)

    async def on_command_error(self, e, ctx):
        try:
            if isinstance(e, checks.No_Perms):
                await ctx.message.channel.send(":no_entry: `You don't have permission to use this command.`")
            elif isinstance(e, checks.No_Owner):
                await ctx.message.channel.send(":no_entry: `Bot Owner Only`")
            elif isinstance(e, checks.No_Mod):
                await ctx.message.channel.send(":no_entry: `Only Server Moderators or Above can use this command`")
            elif isinstance(e, checks.No_Admin):
                await ctx.message.channel.send(":no_entry: `Administrator Only`")
            elif isinstance(e, checks.No_Role):
                await ctx.message.channel.send(":no_entry: `No Custom Role or Specific Permission`")
            elif isinstance(e, checks.No_ServerandPerm):
                await ctx.message.channel.send(":no_entry: `Server specific command or no permission`")
            else:
                if isinstance(e, commands.CommandNotFound):
                    return
        except Exception as e:
            print(e)

    async def wait_until_game_running(self, delay=0):
        if self.debug:
            print("Waiting for the game to run...")
        await self._game_running.wait()
        if delay:
            await asyncio.sleep(delay)

    async def wait_until_game_stopped(self, delay=0):
        if self.debug:
            print("Waiting for the game to stop...")
        await self._game_stopped.wait()
        if delay:
            await asyncio.sleep(delay)

    @property
    def is_game_running(self):
        return self._game_running.is_set()

    @property
    def is_game_stopped(self):
        return self._game_stopped.is_set()

    def bprint(self, text):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        p = text.split("\n")
        for x in p:
            if self.debug:
                print(f"{time} {inspect.stack()[1][3]} ~ {x}")

            else:
                print(f"{Fore.LIGHTYELLOW_EX}{time}{Fore.RESET} ~ {x}")

    def run(self, token):
        super().run(token)

    def die(self):
        try:
            self.loop.stop()
            tasks = asyncio.gather(*asyncio.Task.all_tasks(), loop=self.loop)
            tasks.cancel()
            self.loop.run_forever()
            tasks.exception()
        except Exception as e:
            print(e)
