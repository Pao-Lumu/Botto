import discord, asyncio
from discord.ext import commands
# from .utils.botto_sql import AccountSQL, PastaSQL, GuildSQL
import sqlite3
import os.path
import time


def init_funcs(bot):
    # SQLite3
    global db, cursor
    db_name = 'botto.db'
    if not os.path.exists(db_name):
        db = sqlite3.connect(db_name)
        cursor = db.cursor()
        cursor.execute(
            '''CREATE TABLE pasta(pasta_tag text, pasta_text text, creator_id text, creation_date text, uses integer, likes integer, dislikes integer)''')
        cursor.execute('''CREATE TABLE account(user_id text, bday_day text, bday_month text, bday_year text)''')
        cursor.execute('''CREATE TABLE guild(guild_id text, bday_channel text)''')
    else:
        db = sqlite3.connect(db_name)
        cursor = db.cursor()
    bot.pruned_messages = []
    bot.sqlite.cursor = cursor


class Botto(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.loop = kwargs.pop('loop', asyncio.get_event_loop())
        asyncio.get_child_watcher().attach_loop(self.loop)
        command_prefix = kwargs.pop('command_prefix', commands.when_mentioned_or('.'))
        super().__init__(command_prefix=command_prefix, *args, **kwargs)
        # TODO MAKE CUSTOM HELP THAT DOESN'T LOOK LIKE SHIT
        # self.remove_command('help')

    @property
    def get_cursor(self):
        return cursor
