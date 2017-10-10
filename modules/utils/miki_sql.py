import sqlite3
import os.path

class BaseSQL:
    def __init__(self, filename='botto.db'):
        if not os.path.exists(filename):
            self.db = sqlite3.connect(filename)
            self.cursor = self.db.cursor()
            self.cursor.execute('''CREATE TABLE pasta(pasta_tag text, pasta_text text, creator_id text, creation_date text, uses integer, likes integer, dislikes integer)''')
            self.cursor.execute('''CREATE TABLE account(user_id text, bday_day int, bday_month int, bday_year int)''')
            self.cursor.execute('''CREATE TABLE guild(guild_id int, bday_channel int)''')
        else:
            self.db = sqlite3.connect(filename)
            self.cursor = self.db.cursor()

    def close(self):
        self.db.commit()
        self.db.close()

    def close_no_save(self):
        self.db.close()






# accounts: (user_id text, bday_day int, bday_month int, bday_year int)
class AccountSQL(BaseSQL):
    def add(self, user_id, day=None, month=None, year=None):
        if not self.exists(user_id):
            self.cursor.execute("INSERT INTO account VALUES(?,?,?,?)", (user_id, day, month, year,))
        else:
            self.cursor.execute("UPDATE account SET bday_day=? AND bday_month=? AND bday_year=? WHERE user_id=?", (day, month, year, user_id))
        self.db.commit()

    def exists(self, user_id):
        self.cursor.execute("SELECT * FROM account WHERE user_id=?", (user_id,))
        if self.cursor.fetchone():
            return True
        else:
            return False

    def set_user_birthday(self, user_id, day, month, year):
        self.add(user_id, day, month, year)

    def get_user_birthday(self, user_id):
        if self.exists(user_id):
            self.cursor.execute("SELECT * FROM account WHERE user_id=?", (user_id,))
            return self.cursor.fetchone()
        else:
            return None

    def get_users_with_birthday(self, day, month, guild_id):
        # self.cursor.execute("SELECT * FROM account WHERE bday_day=? AND bday_month=?", (day, month,guild_id))
        self.cursor.execute("SELECT * FROM account WHERE bday_day=? AND bday_month=?", (day, month,))
        return self.cursor.fetchall()

    def get_user_data(self, user_id, field='*'):
        return






# (guild_id int, bday_channel int)
class GuildSQL(BaseSQL):
    def add(self, guild_id, channel_id=None):
        if not self.exists(guild_id):
            self.cursor.execute("INSERT INTO guild VALUES(?,?)", (guild_id, channel_id,))
        else:
            self.cursor.execute("UPDATE guild SET bday_channel=? WHERE guild_id=?", (channel_id, guild_id))
        self.db.commit()

    def exists(self, guild_id):
        self.cursor.execute("SELECT * FROM guild WHERE guild_id=?", (guild_id,))
        if self.cursor.fetchone():
            return True
        else:
            return False

    def set_guild_birthday_channel(self, guild_id, channel_id):
        self.add(guild_id, channel_id)
        return True

    def get_guild_birthday_channel(self, guild_id):
        self.cursor.execute("""SELECT bday_channel FROM guild WHERE guild_id=?""", (guild_id,))
        return self.cursor.fetchone()

    def get_guild_data(self, guild_id, field='*'):
        self.cursor.execute("""SELECT * FROM guild WHERE guild_id=?""", (guild_id,))
        return self.cursor.fetchone()





# (pasta_tag text, pasta_text text, creator_id text, creation_date text, uses integer, likes integer, dislikes integer)
class PastaSQL(BaseSQL):
    def add(self, args: tuple):
        self.cursor.execute('''INSERT INTO pasta VALUES (?,?,?,?,?,?,?)''', args)
        self.db.commit()

    def exists(self, pasta_tag):
        self.cursor.execute("""SELECT * FROM pasta WHERE pasta_tag=?""", (pasta_tag,))
        if self.cursor.fetchone() is None:
            return False
        return True

    def pasta_owned(self, pasta_tag, user_id):
        self.cursor.execute("""SELECT * FROM pasta WHERE pasta_tag=? AND creator_id=?""", (pasta_tag, user_id))
        if self.cursor.fetchone() is None:
            return False
        return True

    def get(self, pasta_tag):
        self.cursor.execute("""SELECT pasta_text,uses FROM pasta WHERE pasta_tag=?""", (pasta_tag,))
        return self.cursor.fetchone()

    def get_owned(self, user_id):
        self.cursor.execute("""SELECT pasta_text,uses FROM pasta WHERE creator_id=?""", (user_id,))
        return self.cursor.fetchall()

    def get_info(self, pasta_tag):
        self.cursor.execute("""SELECT * FROM pasta WHERE pasta_tag=?""", (pasta_tag,))
        return self.cursor.fetchone()

    def delete(self, pasta_tag):
        self.cursor.execute("""DELETE FROM pasta WHERE pasta_tag=?""", (pasta_tag,))
        self.db.commit()

    def update_text(self, pasta_tag, pasta_text):
        self.cursor.execute('''UPDATE pasta SET pasta_text=? WHERE pasta_tag=?''', (pasta_text, pasta_tag))
        self.db.commit()

    def update_uses(self, uses, pasta_tag):
        self.cursor.execute('''UPDATE pasta SET uses=? WHERE pasta_tag=?''', (uses, pasta_tag))
        self.db.commit()

    def popular(self):
        self.cursor.execute('''SELECT pasta_tag,uses FROM pasta ORDER BY uses DESC LIMIT 12''')
        return self.cursor.fetchall()

    def top(self):
        self.cursor.execute('''SELECT pasta_tag,net_vote FROM pasta ORDER BY net_vote DESC LIMIT 12''')
        return

    def vote_up(self, pasta_tag):
        self.cursor.execute('''UPDATE pasta SET dislikes=likes+1, net_vote=net_vote+1''')
        return

    def vote_down(self, pasta_tag):
        self.cursor.execute('''UPDATE pasta SET dislikes=dislikes+1, net_vote=net_vote-1''')
        return

