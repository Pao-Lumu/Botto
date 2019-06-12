import asyncio
import cmd
import datetime
import inspect
import itertools
import platform
import time
import tracemalloc
from pprint import pprint

import colorama
import discord
from colorama import Fore
from discord.ext import commands


class Botto(commands.Bot):
    __slots__ = {'loop', 'cog_folder', 'game', 'gop_text_cd', 'gop_voice_cd', 'debug', 'game_stopped', 'game_running',
                 'chat_channel', 'meme_channel'}

    def __init__(self, *args, **kwargs):
        tracemalloc.start()
        colorama.init()
        self.loop = kwargs.pop('loop', asyncio.get_event_loop())
        self.cog_folder = kwargs.pop('cog_folder')
        self.game = ""
        self.gop_text_cd = 0
        self.gop_voice_cd = 0
        self.in_tmux = False
        if platform.system() == "Linux":
            asyncio.get_child_watcher().attach_loop(self.loop)
        command_prefix = kwargs.pop('command_prefix', commands.when_mentioned_or('.'))
        # self.debug = True
        self.debug = False

        self.game_running = asyncio.Event(loop=self.loop)
        self.game_stopped = asyncio.Event(loop=self.loop)

        super().__init__(command_prefix=command_prefix, *args, **kwargs)

    async def wait_until_ready(self, delay=0):
        if self.debug:
            self.bprint("Waiting for the bot to start...")
        await super().wait_until_ready()
        if delay:
            await asyncio.sleep(delay)

    async def wait_until_game_running(self, delay=0):
        if self.debug:
            print("Waiting for the game to run...")
        await self.game_running.wait()
        if delay:
            await asyncio.sleep(delay)

    async def wait_until_game_stopped(self, delay=0):
        if self.debug:
            print("Waiting for the game to stop...")
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
        # pass

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


# noinspection PyUnusedLocal,PyUnusedLocal
class OGBotCmd(cmd.Cmd):

    __slots__ = {'bot', 'loop', 'completekey', 'attributes', 'vars', 'methods'}

    def __init__(self, loop, bot):
        super().__init__(self)
        self.returns = []
        self.bot = bot
        self.loop = loop
        self.completekey = 'tab'
        self.attributes = [attr for attr in dir(self.bot) if not attr.startswith("__")]
        self.vars = [attr for attr in dir(self.bot) if
                     not callable(getattr(self.bot, attr)) and not attr.startswith("__")]
        self.methods = [attr for attr in dir(self.bot) if
                        callable(getattr(self.bot, attr)) and not attr.startswith("__")]
        self.prompt = f"{Fore.BLUE}{self.bot.user.name} >>>{Fore.RESET}"

    def default(self, line):
        self.do_exec(line)

    # noinspection PyUnusedLocal
    def do_status(self, line):
        """Prints name, uptime, loaded cogs, etc. of the bot."""
        uptime = datetime.datetime.utcnow() - self.bot.uptime
        print(f"""Name: {self.bot.user.name}
Uptime: {str(uptime)}
Loaded cogs: {", ".join(self.bot.cogs.keys())}""")

    def do_reload_cog(self, line):
        """Reloads a module."""
        folder = self.bot.cog_folder
        try:
            if line.find(".") == -1:
                self.bot.unload_extension("{}.{}".format(folder, line))
                self.bot.load_extension("{}.{}".format(folder, line))
            else:
                self.bot.unload_extension(line)
                self.bot.load_extension(line)
        except Exception as e:
            self.bot.bprint('\N{PISTOL}')
            self.bot.bprint('{}: {}'.format(type(e).__name__, e))
        else:
            self.bot.bprint('\N{OK HAND SIGN}')

    def do_reload_all_cogs(self, line):
        """Reloads all modules."""
        temp = self.bot.extensions.keys()
        for ex in temp:
            self.bot.unload_extension(ex)
            self.bot.load_extension(ex)
            pass

    def do_get_methods(self, line):
        """Print all (non-private) methods in self.bot"""
        pprint(self.methods)

    def do_get_vars(self, line):
        """Print all vars in self.bot"""
        pprint(self.vars)

    def do_get_line(self, line):
        """Check how your input is being parsed"""
        print(type(line))
        print(line)

    def do_get_user_info(self, line):
        print(line)
        print(type(line))
        # x = self.bot.fetch_user(int(line))
        x = self.loop.create_task(
            self._exec_async(self.bot.fetch_user, parameters=[int(line)], callback=self._bad_practice))
        while not x.done():
            time.sleep(1)
        time.sleep(.5)
        z = self.returns.pop()
        data = """Name: {} | ID: {}
is_bot: {} | Avatar: {}""".format(z.name, z.id, z.bot, z.avatar_url)
        print(data)

    def do_memory(self, line):

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('size')

        stat = top_stats[0]
        print("%s memory blocks: %.1f KiB" % (stat.count, stat.size / 1024))
        for line in stat.traceback.format():
            print(line)

    def do_exec(self, line):
        """Run methods and return their values, or get the values of variables"""

        try:
            b = line.split(' ')
            func = getattr(self.bot, b[0])
            if callable(func) and b[1:]:
                params = tuple(inspect.signature(func).parameters)
                x = ' '.join(b[1:]).split('|')
                print(f"with parameters {x}")
                if inspect.iscoroutinefunction(func):
                    self.loop.create_task(self._exec_async(func, parameters=x))
                else:
                    try:
                        result = func(*b[1:])
                        print(result) if result else False
                    except RuntimeWarning:
                        pass
                    except TypeError:
                        print(f"Method {b[0]} requires {len(params)} but {len(x)} were given")
                        print(params)
                    else:
                        print(result)
            elif callable(func) and not b[1:]:
                print(f"Calling {b[0]}()")
                if inspect.iscoroutinefunction(func):
                    print('e')
                    self.loop.create_task(self._exec_async(func))
                else:
                    try:
                        result = func()
                        print(result) if result else False
                    except RuntimeWarning:
                        pass
                    except TypeError:
                        params = tuple(inspect.signature(func).parameters)
                        print(f"Method {b[0]} requires {len(params)} but {len(b[1:])} were given")
                        print([params])

            else:
                if func is None:
                    print(f"Var {b[0]}: None")
                else:
                    print(f"Var {b[0]}:")
                    pprint(func)
        except Exception as e:
            print(e)

    def complete_exec(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in self.attributes if s.startswith(mline)]

    def completedefault(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in self.attributes if s.startswith(mline)]

    async def _exec_async(self, method, parameters=None, callback=None):
        try:
            if parameters:
                result = await asyncio.wait_for(method(*parameters), timeout=10)
            else:
                result = await asyncio.wait_for(method(), timeout=10)
            print(result)
            if callback:
                callback(result)
        except Exception as e:
            print(e)

    def _bad_practice(self, result):
        self.returns.append(result)

    def do_set(self, line: str):
        """
        Set the value of a variable
        """

        x = line.split(" ", maxsplit=1)
        if len(x) is not 2:
            print("Please give a value to set the variable to.")
            return
        elif not hasattr(self.bot, x[0]):
            setattr(self.bot, x[0], x[1])
            print(f"Added attribute {x[0]} to {x[1]}")
            return
        else:
            var = getattr(self.bot, x[0])
            if isinstance(var, str):
                setattr(self.bot, x[0], str(x[1]))
            elif isinstance(var, int):
                setattr(self.bot, x[0], int(x[1]))
            elif isinstance(var, list):
                var = x[1].split(',')
                setattr(self.bot, x[0], var)

            else:
                print(f'Your variable typing is too strong! (Variable of type {type(var)} couldn\'t be processed)')

    def complete_set(self, text, line):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in self.vars if s.startswith(mline)]

    def do_exit(self, line):
        return True

    def do_stop(self, line):
        return True

    async def start(self):
        await self.loop.run_in_executor(None, self.cmdloop)
