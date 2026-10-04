from engine.timeline import Scene
from .. import script as SC


class Quantique(Scene):
    id = 'quantique'
    chapter = ('09', 'La frontière quantique')
    lead = 2.4

    def lines(self):
        return SC.QUANTIQUE

    def draw(self, p, S):
        pass
