from engine.timeline import Scene
from .. import script as SC


class Transistor(Scene):
    id = 'transistor'
    chapter = ('04', 'Le transistor')
    lead = 2.4

    def lines(self):
        return SC.TRANSISTOR

    def draw(self, p, S):
        pass
