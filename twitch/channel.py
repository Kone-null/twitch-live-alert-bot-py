class Channel:
    def __init__(self, name: str = "", live: bool = False):
        self.name = name
        self.live = live

    def set_live(self) -> None:
        self.live = True

    def set_offline(self) -> None:
        self.live = False

    def data(self) -> dict:
        return {"name": self.name, "live": self.live}
    

