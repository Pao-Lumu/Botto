from discord.ext import commands


class OGBotCommand(commands.Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, kwargs=kwargs)

    def invoke(self, ctx, cli=False):
        if cli:
            pass


class OGBotContext(commands.Context):
    def __init__(self, **attrs):
        super().__init__(attrs=attrs)
