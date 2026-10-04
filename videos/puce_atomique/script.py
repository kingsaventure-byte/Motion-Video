"""Voix off — « Au cœur du silicium ».

Texte écrit pour l'oral : les nombres et unités sont en toutes lettres pour une
prononciation naturelle ; les écrans affichent les notations scientifiques.
`pause` = silence après la réplique (secondes).
"""
from engine.timeline import Line as L

INTRO = [
    L('i1', "En ce moment même, dans l'appareil que vous tenez entre les mains, des dizaines de milliards "
            "d'interrupteurs microscopiques s'allument et s'éteignent, des milliards de fois par seconde.", 0.7),
    L('i2', "Rien ne bouge. Aucune pièce ne tourne.", 0.35),
    L('i3', "Et pourtant, à l'intérieur, tout est mouvement.", 0.8),
    L('i4', "Plongeons au cœur du silicium, jusqu'à l'échelle des atomes, pour comprendre ce qui se passe "
            "vraiment quand une puce calcule.", 0.5),
]

ECHELLE = [
    L('e1', "Voici un processeur. Sous son capot métallique se cache une fine plaque de silicium, "
            "à peine plus grande qu'un ongle : la puce.", 0.5),
    L('e2', "Elle est organisée comme une ville, avec ses quartiers : les cœurs de calcul, la mémoire cache, "
            "le processeur graphique, les circuits d'entrée et de sortie.", 0.5),
    L('e3', "Zoomons dans un cœur. Puis encore. Et encore.", 0.6),
    L('e4', "Apparaissent alors des forêts de transistors, alignés par dizaines de milliards.", 0.45),
    L('e5', "Leurs parties les plus fines ne mesurent que quelques nanomètres : "
            "à peine quelques dizaines d'atomes de large.", 0.5),
]

SILICIUM = [
    L('s1', "Tout commence avec un élément : le silicium.", 0.45),
    L('s2', "Un atome de silicium possède quatorze électrons. Mais seuls les quatre de sa couche externe "
            "participent aux liaisons.", 0.45),
    L('s3', "Il partage ces quatre électrons avec quatre voisins. Chaque liaison est une paire d'électrons "
            "mise en commun.", 0.45),
    L('s4', "Répété des milliards de milliards de fois, ce motif forme un cristal d'une régularité parfaite.", 0.5),
    L('s5', "Dans ce cristal, presque chaque électron est prisonnier d'une liaison. "
            "Le silicium pur conduit donc très mal le courant...", 0.25),
    L('s6', "et c'est justement ce qui le rend si précieux : on va pouvoir décider, avec une précision extrême, "
            "où et quand il conduira.", 0.5),
]

DOPAGE = [
    L('d1', "Pour le rendre conducteur, on y introduit des atomes étrangers, en quantité infime. "
            "C'est le dopage.", 0.45),
    L('d2', "Remplaçons un atome de silicium par un atome de phosphore. Il possède cinq électrons externes : "
            "quatre forment les liaisons... le cinquième est de trop.", 0.4),
    L('d3', "Faiblement retenu, il se libère et se met à errer dans le cristal. C'est un porteur de charge "
            "négative : on parle de silicium de type N.", 0.6),
    L('d4', "À l'inverse, un atome de bore n'a que trois électrons externes. Il en manque un dans une liaison : "
            "c'est un trou.", 0.4),
    L('d5', "Un électron voisin vient combler ce trou... laissant un nouveau trou derrière lui. "
            "Le trou se déplace, comme une charge positive : c'est le silicium de type P.", 0.5),
    L('d6', "Il suffit parfois d'un seul atome étranger pour des millions d'atomes de silicium "
            "pour changer radicalement son comportement.", 0.5),
]

TRANSISTOR = [
    L('t1', "Avec ces deux ingrédients, on construit la brique de base de toute l'informatique : "
            "le transistor.", 0.45),
    L('t2', "Deux zones riches en électrons libres, la source et le drain, sont séparées par une région "
            "de type P.", 0.4),
    L('t3', "Juste au-dessus, une électrode, la grille, isolée par une couche d'oxyde épaisse de quelques "
            "atomes seulement.", 0.5),
    L('t4', "Au repos, les électrons de la source se heurtent à une barrière d'énergie : ils ne peuvent pas "
            "passer. Le transistor est bloqué. C'est un zéro.", 0.6),
    L('t5', "Appliquons maintenant une petite tension sur la grille, moins d'un volt. Son champ électrique "
            "traverse l'oxyde, repousse les trous, et attire les électrons juste sous la surface.", 0.4),
    L('t6', "Une fine couche conductrice se forme : le canal. La barrière s'abaisse, et les électrons "
            "s'engouffrent de la source vers le drain. Le courant passe. C'est un un.", 0.6),
    L('t7', "Coupez la tension, et le canal disparaît en quelques picosecondes. Zéro. Un. Zéro. "
            "Voilà, physiquement, ce qu'est un bit.", 0.5),
]

ELECTRONS = [
    L('v1', "Mais à quoi ressemble vraiment le trajet d'un électron dans ce canal ?", 0.45),
    L('v2', "Même sans tension, il n'est jamais immobile. L'agitation thermique le projette dans toutes "
            "les directions, à plus de cent kilomètres par seconde.", 0.4),
    L('v3', "Il rebondit sans cesse sur les atomes qui vibrent et sur les impuretés. "
            "Une course chaotique, sans direction.", 0.5),
    L('v4', "Quand une tension est appliquée, le champ électrique incline ce chaos. Le mouvement reste "
            "désordonné, mais il gagne une direction : c'est la dérive.", 0.45),
    L('v5', "Dans un canal de quelques dizaines de nanomètres, la traversée ne dure qu'une fraction "
            "de picoseconde.", 0.6),
    L('v6', "Dans les fils de cuivre qui relient les transistors, en revanche, les électrons avancent "
            "en moyenne à moins d'un mètre par seconde.", 0.45),
    L('v7', "Ce qui voyage vite, ce n'est pas l'électron, c'est le signal. Comme dans un tube déjà rempli "
            "de billes : poussez-en une d'un côté, et une autre sort aussitôt de l'autre.", 0.5),
]

PORTES = [
    L('l1', "Un transistor seul ne calcule rien. Toute la magie vient de leur association.", 0.45),
    L('l2', "Relions un transistor de type N à son jumeau de type P : on obtient un inverseur. "
            "Quand l'entrée vaut un, la sortie vaut zéro. Et inversement.", 0.45),
    L('l3', "À chaque basculement, la sortie se charge ou se décharge : quelques centaines à quelques "
            "milliers d'électrons transitent, à chaque fois.", 0.5),
    L('l4', "Avec quatre transistors, on construit une porte NON-ET. Et à partir de portes NON-ET, "
            "on peut construire absolument tous les circuits logiques.", 0.45),
    L('l5', "Un additionneur, par exemple : quelques dizaines de transistors suffisent pour additionner "
            "deux bits. Quelques milliers, pour additionner deux nombres de soixante-quatre bits... "
            "en une fraction de nanoseconde.", 0.5),
]

HORLOGE = [
    L('h1', "Pour que ces milliards de basculements restent coordonnés, la puce suit un métronome : "
            "l'horloge.", 0.45),
    L('h2', "À quatre gigahertz, elle bat quatre milliards de fois par seconde. Un seul battement dure "
            "un quart de nanoseconde.", 0.45),
    L('h3', "Pendant ce laps de temps, même la lumière ne parcourt que sept centimètres et demi.", 0.55),
    L('h4', "À chaque battement, une vague d'activité traverse la puce : les données avancent d'une étape, "
            "des millions de transistors basculent en cascade... puis tout se stabilise, "
            "jusqu'au battement suivant.", 0.5),
]

CHALEUR = [
    L('c1', "Mais tout ce mouvement a un prix.", 0.4),
    L('c2', "À chaque collision, les électrons cèdent un peu de leur énergie aux atomes du cristal, "
            "qui se mettent à vibrer plus fort.", 0.35),
    L('c3', "Ces vibrations, c'est de la chaleur.", 0.55),
    L('c4', "Multipliées par des milliards de transistors et des milliards de cycles par seconde, "
            "elles représentent des dizaines, voire des centaines de watts, concentrés sur quelques "
            "centimètres carrés.", 0.45),
    L('c5', "Par centimètre carré, c'est jusqu'à dix fois plus qu'une plaque de cuisson. "
            "D'où les dissipateurs, les ventilateurs, et parfois le refroidissement liquide.", 0.5),
]

QUANTIQUE = [
    L('q1', "Et plus on miniaturise, plus on se heurte aux lois étranges de la physique quantique.", 0.45),
    L('q2', "À cette échelle, un électron ne se comporte plus seulement comme une bille, "
            "mais aussi comme une onde.", 0.45),
    L('q3', "Face à une barrière de quelques atomes d'épaisseur, une partie de cette onde passe "
            "de l'autre côté : c'est l'effet tunnel.", 0.45),
    L('q4', "Des électrons fuient alors à travers l'isolant, même quand le transistor est censé être bloqué. "
            "De l'énergie gaspillée, et de la chaleur en plus.", 0.5),
    L('q5', "Pour résister, les ingénieurs ont réinventé le transistor : des isolants plus performants, "
            "une grille qui enveloppe le canal sur trois côtés, le FinFET... et désormais sur ses quatre faces, "
            "avec les transistors à grille enveloppante.", 0.5),
]

FINALE = [
    L('f1', "Alors, la prochaine fois que vous ouvrez une application, regardez une vidéo, "
            "ou envoyez un simple message...", 0.2),
    L('f2', "souvenez-vous qu'au fond de la puce, des milliards d'électrons viennent d'exécuter, pour vous, "
            "une chorégraphie d'une précision inouïe.", 0.8),
    L('f3', "Rien ne bouge. Et pourtant, tout est mouvement.", 0.5),
]
