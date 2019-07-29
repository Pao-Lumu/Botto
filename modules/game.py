import asyncio
import functools

from discord.ext.commands import Cog

from utils import Server as srv
from utils import sensor as sensor


class Game(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.get_current_server_status())
        self.bot.loop.create_task(self.check_server_running())

    async def check_server_running(self):
        await self.bot.wait_until_ready(1)
        while not self.bot.is_closed():

            process, data = sensor.get_game_info()
            if data:
                self.bot._game_stopped.clear()
                self.bot._game_running.set()

                self.bot.bprint(f"Server Status | Now Playing: {data['name']} {data['version']}")
                # await self.bot.loop.run_in_executor(None, process.wait)
                print('t')
                # x = self.bot.loop.run_in_executor(None, self.wait_or_when_cancelled)
                await self.bot.loop.run_in_executor(None, functools.partial(self.wait_or_when_cancelled, process))
                self.bot.bprint(f"Server Status | Offline")

                self.bot._game_running.clear()
                self.bot._game_stopped.set()
            else:
                await asyncio.sleep(5)

    def wait_or_when_cancelled(self, process):
        while not self.bot.is_closed() and process.is_running():
            process.wait(timeout=1)

    async def get_current_server_status(self):
        await self.bot.wait_until_game_running(1)
        self.bot.game = None
        while not self.bot.is_closed():
            process, data = sensor.get_game_info()

            # If game is running upon instantiation
            if self.bot.is_game_running:
                self.bot.game = srv.generate_server_object(self.bot, process, data)
                await self.bot.wait_until_game_stopped(2)

            # Elif no game is running upon instantiation:
            elif self.bot.is_game_stopped:
                self.bot.game = None
                await self.bot.change_presence()
                await self.bot.wait_until_game_running(2)


def setup(bot):
    bot.add_cog(Game(bot))
