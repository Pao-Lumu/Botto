from contextlib import asynccontextmanager

from discord import Activity, Spotify, CustomActivity, ActivityType, DMChannel, TextChannel, VoiceChannel, \
    ClientException
from discord.ext.commands import Command

import utils.errors


class MiniActivity:

    def __init__(self, ob: Activity):
        self.ob = ob
        self.type = ob.type
        self.name = ob.name
        if isinstance(ob, Spotify):
            self.artist = ob.artist
            self.title = ob.title
            self.track_id = ob.track_id
        if isinstance(ob, CustomActivity):
            self.emoji = ob.emoji

    def __eq__(self, other):
        try:
            if self.name != other.name or other.type != self.type:
                return False
            elif self.name == other.name and self.type == ActivityType.listening:
                if self.track_id == other.track_id:
                    return True
                else:
                    return False
            else:
                return True
        except TypeError:
            print("FAIL")
            return False

    def __hash__(self):
        if self.type == ActivityType.listening:
            return hash((self.type, self.name, self.artist, self.title, self.track_id))
        else:
            return hash((self.type, self.name))

    def __str__(self):
        if self.type == ActivityType.listening:
            return f"MiniActivity object (type='{self.type.name}',title='{self.title}', artist='{self.artist}')"
        else:
            return f"MiniActivity object (type='{self.type.name}',name='{self.name}')"

    def __repr__(self):
        if self.type == ActivityType.listening:
            return f"MiniActivity object (type='{self.type.name}',title='{self.title}', artist='{self.artist}')"
        else:
            return f"MiniActivity object (type='{self.type.name}',name='{self.name}')"


class MiniChannel:

    def __init__(self, channel):
        self.id = channel.id
        if isinstance(channel, DMChannel):
            self.name = "DM from " + channel.recipient.name
        elif isinstance(channel, TextChannel):
            self.name = channel.name
        elif isinstance(channel, VoiceChannel):
            self.name = channel.name


def check(predicate):
    def decorator(func):
        if isinstance(func, Command):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__commands_checks__'):
                func.__commands_checks__ = []

            func.__commands_checks__.append(predicate)

        return func

    return decorator


def is_human():
    async def predicate(ctx):
        if ctx.author.bot:
            raise utils.errors.NotHuman('Message not sent by a human')
        return True

    return check(predicate)


class VoiceChatContext:
    def __init__(self, ctx):
        self.ctx = ctx

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await print("Bye!")

    async def __aenter__(self):
        pass

    @asynccontextmanager
    async def is_valid_voicechat(self):
        try:
            if self.ctx.author.voice.channel and not self.ctx.author.voice.afk:
                vc = await self.ctx.author.voice.channel.connect()
                try:
                    yield vc
                finally:
                    vc.stop()
                    await vc.disconnect()

            elif self.ctx.author.voice.afk:
                await self.ctx.send("Bot cannot play music in AFK channels. Move to a non-AFK channel and try again.")
        except ClientException as e:
            print(e)
            await self.ctx.send("Bot's host system is missing required programs. Please notify the administrator.")
        except AttributeError as e:
            print(e)
            await self.ctx.send("Not in a voice channel, or unable to access current voice channel.")
        except OSError as e:
            print(e)
            print("Hey lotus why don't you eat a fucking dick ~ Zach 2018")
