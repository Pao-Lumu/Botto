import asyncio
import datetime
import inspect
import itertools
import platform
import tracemalloc

import colorama
import discord
from colorama import Fore
from discord.ext import commands


class OGBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        tracemalloc.start()
        colorama.init()
        self.loop = kwargs.pop('loop', asyncio.get_event_loop())
        self.cog_folder = kwargs.pop('cog_folder')
        self.game = ""
        self.gwd = ""
        self.gop_text_cd = 0
        self.gop_voice_cd = 0
        self.in_tmux = False
        self.debug = False
        # self.debug = True
        self.game_running = asyncio.Event(loop=self.loop)
        self.game_stopped = asyncio.Event(loop=self.loop)
        command_prefix = kwargs.pop('command_prefix', commands.when_mentioned_or('.'))
        if platform.system() == "Linux":
            asyncio.get_child_watcher().attach_loop(self.loop)
        super().__init__(command_prefix=command_prefix, *args, **kwargs)

    # def debuggable(debug_text):
    #     def decorator(func):
    #         def wrapper(self, delay=0):
    #             if self.debug:
    #                 print(debug_text)
    #             return asyncio.create_task(func(delay))
    #         return wrapper
    #     return decorator

    # @debuggable("Waiting for the bot to start...")
    async def wait_until_ready(self, delay=0):
        await super().wait_until_ready()
        if delay:
            await asyncio.sleep(delay)

    # @debuggable("Waiting for the game to run...")
    async def wait_until_game_running(self, delay=0):
        await self.game_running.wait()
        if delay:
            await asyncio.sleep(delay)

    # @debuggable("Waiting for the game to stop...")
    async def wait_until_game_stopped(self, delay=0):
        await self.game_stopped.wait()
        if delay:
            await asyncio.sleep(delay)

    async def set_bot_status(self, line1: str, line2: str, line3: str, *args, **kwargs):
        padder = [line1.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line1))))
                  + line2.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line2))))
                  + line3.replace(' ', '\u00a0')]
        await self.change_presence(activity=discord.Game(f"{' '.join(padder)}"))

    async def get_loaded_cogs(self):
        return self.cogs

    @property
    def is_game_running(self):
        return self.game_running.is_set()

    @property
    def is_game_stopped(self):
        return self.game_stopped.is_set()

    def bprint(self, text, *args):
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = text.split("\n")
        for line in lines:
            if self.debug:
                print(f"{cur_time} {inspect.stack()[1][3]} ~ {line}", *args)

            else:
                print(f"{Fore.LIGHTYELLOW_EX}{cur_time}{Fore.RESET} ~ {line}", *args)

    def run(self, token):
        super().run(token)

    async def die(self):
        await self.close()

    async def close(self):
        try:
            await super().close()
            tasks = asyncio.gather(*asyncio.Task.all_tasks(), loop=self.loop)
            tasks.cancel()
            tasks.exception()
            self.loop.stop()
        except:
            pass