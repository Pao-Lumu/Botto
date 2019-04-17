from discord import Activity, Spotify


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
            if other.type == self.type:
                pass
