class Debug:
    def __init__(self, cfg):
        self.cfg = cfg
        self.clock = cfg["clock"]

    def loop(self):
        print(self.clock.main_session())
        print(self.clock.timestr_UTC)
        print(self.clock.session())
        print("Testing")