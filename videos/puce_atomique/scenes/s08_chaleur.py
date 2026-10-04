from engine.timeline import Scene
from .. import script as SC


class Chaleur(Scene):
    id = 'chaleur'
    chapter = ('08', 'La chaleur')
    lead = 2.4

    def lines(self):
        return SC.CHALEUR

    def draw(self, p, S):
        pass
