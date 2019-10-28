from discord.ext.commands import errors


class OGBotException(Exception):
    pass


class NotHuman(OGBotException, errors.CommandError):
    pass
