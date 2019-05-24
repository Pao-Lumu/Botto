import asyncio
import cmd
import datetime
import inspect
import itertools
import platform
from pprint import pprint

import colorama
import discord
from colorama import Fore
from discord.ext import commands

from utils import checks


class Botto(commands.Bot):
    __slots__ = {'loop', 'cog_folder', 'game', 'gop_text_cd', 'gop_voice_cd', 'debug', '_game_stopped', '_game_running',
                 'chat_channel', 'meme_channel'}

    def __init__(self, *args, **kwargs):
        colorama.init()
        self.loop = kwargs.pop('loop', asyncio.get_event_loop())
        self.cog_folder = kwargs.pop('cog_folder')
        self.game = ""
        self.gop_text_cd = 0
        self.gop_voice_cd = 0
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

    async def set_bot_status(self, line1: str, line2: str, line3: str, *args, **kwargs):
        padder = [line1.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line1))))
                  + line2.replace(' ', '\u00a0'), ''.join(list(itertools.repeat('\u3000', 40 - len(line2))))
                  + line3.replace(' ', '\u00a0')]
        await self.change_presence(activity=discord.Game(f"{' '.join(padder)}"))

    @property
    def is_game_running(self):
        return self._game_running.is_set()

    @property
    def is_game_stopped(self):
        return self._game_stopped.is_set()

    def bprint(self, text, *args):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        p = text.split("\n")
        for x in p:
            if self.debug:
                print(f"{time} {inspect.stack()[1][3]} ~ {x}", *args)

            else:
                print(f"{Fore.LIGHTYELLOW_EX}{time}{Fore.RESET} ~ {x}", *args)

    def run(self, token):
        super().run(token)

    async def die(self):
        await self.close()
    #
    # async def close(self):
    #     try:
    #         await super().close()
    #         self.loop.stop()
    #         tasks = asyncio.gather(*asyncio.Task.all_tasks(), loop=self.loop)
    #         tasks.cancel()
    #     except Exception as e:
    #         print(e)


class OGBotCmd(cmd.Cmd):
    prompt = f"{Fore.BLUE}OGBot >>>{Fore.RESET}"

    __slots__ = {'bot', 'loop', 'completekey', 'attributes', 'vars', 'methods'}

    def __init__(self, loop, bot):
        super().__init__(self)
        self.bot = bot
        self.loop = loop
        self.completekey = 'tab'
        self.attributes = [attr for attr in dir(self.bot) if not attr.startswith("__")]
        self.vars = [attr for attr in dir(self.bot) if
                     not callable(getattr(self.bot, attr)) and not attr.startswith("__")]
        self.methods = [attr for attr in dir(self.bot) if
                        callable(getattr(self.bot, attr)) and not attr.startswith("__")]

    def default(self, line):
        self.do_exec(line)

    def do_status(self, line):
        uptime = datetime.datetime.utcnow() - self.bot.uptime
        print(f"""Name: {self.bot.name}
Uptime: {str(uptime)}""")


    def do_get_methods(self, line):
        """Print all (non-private) methods in self.bot"""
        pprint(self.methods)

    def do_get_vars(self, line):
        """Print all vars in self.bot"""
        pprint(self.vars)

    def do_get_line(self, line):
        """Check how your input is being parsed"""
        print(line)

    def do_exec(self, line):
        """Run methods and return their values, or get the values of variables"""

        try:
            b = line.split(' ')
            func = getattr(self.bot, b[0])
            params = tuple(inspect.signature(func).parameters)
            print(f"Calling {b[0]}")
            print(params) if params else False
            if callable(func) and b[1:]:
                # x = '\u00A0'.join(b[1:]).split('|')
                x = ' '.join(b[1:]).split('|')
                # x = b[1:]
                print(f"with parameters {x}")
                if inspect.iscoroutinefunction(func):
                    print('e')
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
                        print(params)

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

    async def _exec_async(self, method, parameters=None):
        try:
            if parameters:
                result = await asyncio.wait_for(method(*parameters), timeout=10)
            else:
                result = await asyncio.wait_for(method(), timeout=10)
            print(result)
        except Exception as e:
            print(e)

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
