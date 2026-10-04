from engine.timeline import Scene
from .. import script as SC


class Portes(Scene):
    id = 'portes'
    chapter = ('06', 'La logique')
    lead = 2.4

    def lines(self):
        return SC.PORTES

    def draw(self, p, S):
        pass
