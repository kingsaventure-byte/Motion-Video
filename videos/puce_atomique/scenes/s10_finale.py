from engine.timeline import Scene
from .. import script as SC


class Finale(Scene):
    id = 'finale'
    lead = 1.2

    def lines(self):
        return SC.FINALE

    def draw(self, p, S):
        pass
