import evtman
from events import QuitEvent

class UiController(evtman.SingleListener):
    def onQuitRequest(self, unused):
        self.post(QuitEvent())
