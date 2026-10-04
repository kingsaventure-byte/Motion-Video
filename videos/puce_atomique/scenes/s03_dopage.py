from engine.timeline import Scene
from .. import script as SC


class Dopage(Scene):
    id = 'dopage'
    chapter = ('03', 'Le dopage')
    lead = 2.4

    def lines(self):
        return SC.DOPAGE

    def draw(self, p, S):
        pass
