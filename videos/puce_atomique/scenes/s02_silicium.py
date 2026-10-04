from engine.timeline import Scene
from .. import script as SC


class Silicium(Scene):
    id = 'silicium'
    chapter = ('02', 'Le silicium')
    lead = 2.4

    def lines(self):
        return SC.SILICIUM

    def draw(self, p, S):
        pass
