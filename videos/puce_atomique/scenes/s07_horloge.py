from engine.timeline import Scene
from .. import script as SC


class Horloge(Scene):
    id = 'horloge'
    chapter = ('07', "L'horloge")
    lead = 2.4

    def lines(self):
        return SC.HORLOGE

    def draw(self, p, S):
        pass
