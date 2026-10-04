"""Charte graphique de la vidéo."""
from engine.color import hex2

BG_IN = hex2('#0A1430')
BG_OUT = hex2('#020309')

TEXT = hex2('#EEF3FF')
TEXT2 = hex2('#9AA8C9')
TEXT3 = hex2('#5B6890')
LINE = hex2('#3A4A72')

CYAN = hex2('#38E1FF')        # électrons
CYAN_HOT = hex2('#D8FAFF')
BLUE = hex2('#3D7BFF')
AMBER = hex2('#FFB547')       # trous
ORANGE = hex2('#FF7A2F')
VIOLET = hex2('#9277FF')      # champ électrique
SI = hex2('#8193C0')          # atomes de silicium
SI_DARK = hex2('#2B395E')
PHOS = hex2('#6CFFB4')        # phosphore
BORON = hex2('#FF5F94')       # bore
COPPER = hex2('#E8955A')
GOLD = hex2('#D9B46C')
GREEN = hex2('#5CFFA0')
RED = hex2('#FF4D5E')
WHITE = (1.0, 1.0, 1.0, 1.0)

HEAT = [(0.0, hex2('#2E4C9A')), (0.35, hex2('#B2357A')), (0.6, hex2('#FF6A2E')),
        (0.85, hex2('#FFC14D')), (1.0, hex2('#FFF6D8'))]
