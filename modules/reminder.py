from datetime import datetime

from discord.ext import commands, tasks


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._remind_check.start()
        self._temp_reminder.start()

    @tasks.loop(minutes=5)
    async def _temp_reminder(self):
        t = datetime.now().time()
        if 1 < t.hour <= 3:
            await self.temporary_reminding_method()
        # await self.temporary_reminding_method()

    @tasks.loop(seconds=59)
    async def _remind_check(self):
        t = datetime.now().time()
        print(t)

    async def temporary_reminding_method(self):
        await self.bot.wait_until_ready()
        try:
            for pp in self.bot.get_all_members():
                owner = pp if pp.id == self.bot.owner_id else None
                if owner:
                    break
            if owner.activities:
                await owner.send("Hey Evan go to bed.", tts=True)
        except Exception as e:
            print(e)
            print('smd')

    # @commands.command(aliases=['remindme', 'remindmeto', 'rmt'])
    # async def remind(self, ctx, *, args):
    # x = {"reminders": [{"wash the dishes": {"hour":12, "minute": "5", "second": "32"}}]}
    # general format should be: >remindmeto go to bed at 1:00 AM daily/on the weekend/on Wednesday
    # datelookup = {"daily": "", "sunday": "", "monday": "", "tuesday": "",
    #               "wednesday": "", "thursday": "", "friday": "",
    #               "saturday": "", "weekdays": "", "weekends": "", "today": ""}
    # timelookup = {"AM": "", "PM": "", "noon": time(hour=12), "midnight": time(hour=0), "sunrise": "", "sunset": ""}
    # modifiers = {"except", "first", "second", "third", "fourth", "final"}
    #
    # test = str(args).split(' at ')
    # while len(test) > 2:
    #     test[0] = " at ".join(test[0:2])
    #     test.pop(1)
    # message, date = test
    # print(f"{message}: {date}")
    # self._analyze(date)

    # def _analyze(self, date):
    #     if ':' in date:
    #         hours, others = date.split(':')
    #         minutes = others[0:2]
    #         others = others[2:]

    # pass

    # @commands.group()
    # async def example_group(self, ctx):
    #     if ctx.subcommand_passed:
    #         pass
    #     else:
    #         pass
    #
    # @example_group.command()
    # async def example_subcommand(self, ctx):
    #     pass


def setup(bot: commands.Bot):
    bot.add_cog(Reminder(bot))
