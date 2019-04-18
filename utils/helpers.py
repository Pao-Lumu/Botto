from discord import Activity, Spotify, ActivityType


class MiniActivity:

    def __init__(self, ob: Activity):
        self.ob = ob
        self.type = ob.type
        self.name = ob.name
        if isinstance(ob, Spotify):
            self.artist = ob.artist
            self.title = ob.title
            self.track_id = ob.track_id

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
        except:
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
