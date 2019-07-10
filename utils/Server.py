class Server:
    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        self.name = kwargs.pop('name', 'a game')
        self.ip = kwargs.pop('ip', '127.0.0.1')
        self.port = kwargs.pop('port', '22222')
        self.password = kwargs.pop('password', '')
        self.working_dir = kwargs.pop('working_dir', '')
        self.process_id = kwargs.pop('process_id', -1)

    async def chat_from_server_to_discord(self): pass

    async def chat_to_server_from_discord(self): pass

    async def update_server_information(self):
        self.bot.set_bot_status(self.name)


class MinecraftServer(Server):
    def __init__(self, bot, *args, **kwargs):
        self.motd = kwargs.pop('motd')
        super().__init__(bot, args=args, kwargs=kwargs)

    async def chat_from_server_to_discord(self):
        pass

    async def chat_to_server_from_discord(self):
        pass

    async def update_server_information(self):
        self.bot.set_bot_status(self.name)
