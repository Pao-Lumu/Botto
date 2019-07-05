import asyncio
from datetime import datetime

from discord.ext import commands, tasks


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lock = asyncio.Lock(loop=bot.loop)
        self.alarm.start(**{'proc': True})

    @tasks.loop(minutes=5)
    async def alarm(self, *args, **kwargs):
        proc = kwargs.pop('proc', False)
        if proc:
            self.alarm.change_interval(minutes=5)
            dt = datetime.now()
            t = dt.time()
            d = dt.date()
            # Mon = 0, Tues = 1, etc.
            async with self.lock:
                if d.weekday() < 5:
                    if 1 <= t.hour <= 3:
                        self.bot.loop.create_task(self.alarm_beep())

    @alarm.after_loop
    async def before_alarm(self):
        await self.bot.wait_until_ready()

    async def alarm_beep(self):
        await self.bot.wait_until_ready()
        try:
            for pp in self.bot.get_all_members():
                owner = pp if pp.id == self.bot.owner_id else None
                if owner:
                    break
            if owner.activities:
                beep = await owner.send("Go to bed.", tts=True)
                await self.bot.wait_for('message', check=lambda m: m.channel.id == beep.channel.id, timeout=301)
                self.alarm.cancel()
                self.alarm.change_interval(minutes=1)
                self.alarm.restart(**{'proc': False})

        except TimeoutError:
            return
        except Exception as e:
            print(e)

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
