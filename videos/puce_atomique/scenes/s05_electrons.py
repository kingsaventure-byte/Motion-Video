from engine.timeline import Scene
from .. import script as SC


class Electrons(Scene):
    id = 'electrons'
    chapter = ('05', "Le voyage d'un électron")
    lead = 2.4

    def lines(self):
        return SC.ELECTRONS

    def draw(self, p, S):
        pass
