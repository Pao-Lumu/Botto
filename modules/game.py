# noinspection PyPackageRequirements
import asyncio
import os
from difflib import SequenceMatcher

import discord
from discord.ext import commands

from utils import helpers
import asyncio
import functools

import psutil

from utils import Server as srv
from utils import sensor


class Game(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.check_server_running())
        self.bot.loop.create_task(self.get_current_server_status())

    @staticmethod
    def wait_or_when_cancelled(process):
        bot_proc = psutil.Process()
        while True:
            try:
                process.wait(timeout=1)
                return
            except psutil.TimeoutExpired:
                if bot_proc.is_running():
                    continue
                else:
                    return

    async def check_server_running(self):
        await self.bot.wait_until_ready(1)
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(1)
                process, data = sensor.get_game_info()
                if process and data:
                    self.bot._game_stopped.clear()
                    self.bot._game_running.set()
                    self.bot.gameinfo = data

                    self.bot.bprint(f"Server Status | Now Playing: {data['name']}")
                    await self.bot.loop.run_in_executor(None, functools.partial(self.wait_or_when_cancelled, process))
                    self.bot.bprint(f"Server Status | Offline")

                    self.bot._game_running.clear()
                    self.bot._game_stopped.set()
                    self.bot.gameinfo = None
            except ProcessLookupError:
                await asyncio.sleep(5)
                continue
            except ValueError:
                await asyncio.sleep(5)
                continue
            except AttributeError:
                await asyncio.sleep(5)
                continue
            except Exception as e:
                print(str(type(e)) + ": " + str(e))
                print("This is from the server checker")

    async def get_current_server_status(self):
        await self.bot.wait_until_game_running(1)
        self.bot.game = None
        while not self.bot.is_closed():
            # If game is running upon instantiation
            if self.bot.is_game_running:
                process, data = sensor.get_game_info()
                self.bot.game = srv.generate_server_object(self.bot, process, data)
                await self.bot.wait_until_game_stopped(2)

            # Elif no game is running upon instantiation:
            elif self.bot.is_game_stopped:
                self.bot.game = None
                await self.bot.change_presence()
                await self.bot.wait_until_game_running(2)


def setup(bot):
    bot.add_cog(Game(bot))
