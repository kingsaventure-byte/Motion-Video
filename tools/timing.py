"""Affiche le minutage des scènes, répliques et mots (aide à l'animation)."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
from videos.puce_atomique.video import make
v = make().prepare(tts=False)
want = sys.argv[1:] 
for sc in v.scenes:
    print(f'== {sc.id:12s} start {sc.start:7.2f}  dur {sc.dur:6.2f}  end {sc.end:7.2f}')
    if want and sc.id not in want:
        continue
    for ln in sc._lines:
        print(f'   {ln.id:4s} {ln.start:6.2f}-{ln.end:6.2f} | ' + ' '.join(f'{w}@{s:.2f}' for w, s, e in ln.words))
print('TOTAL', round(v.duration, 2))
