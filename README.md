# Motion-Video

Studio de vidéos explicatives en motion design, avec un **moteur de rendu maison** écrit en Python.

## Le moteur (`engine/`)

| Module | Rôle |
|---|---|
| `ease.py`, `anim.py` | Courbes d'accélération (Bézier façon CSS, ressorts), tweens, keyframes |
| `painter.py` | Canevas à double tampon : l'image + un tampon d'émission (halo lumineux), sprites en lot, typographie animée |
| `text.py` | Mise en forme HarfBuzz (crénage, ligatures), exposants `^{}` et indices `_{}` |
| `camera.py`, `mesh.py` | Caméra 2D, projection 3D en perspective, pavés ombrés (algorithme du peintre) |
| `post.py` | Post-traitement : halo multi-échelle, bloom, tone mapping, aberration chromatique, vignette, grain |
| `timeline.py`, `video.py` | Scènes, répliques, synchronisation **au mot près** avec la voix off, transitions |
| `tts.py` | Voix off Edge TTS (`fr-FR-RemyMultilingualNeural`, 96 kbit/s), horodatage de chaque mot, cache |
| `render.py` | Rendu multiprocessus → ffmpeg (H.264, BT.709) |

Skia sert uniquement de rastériseur (le « GPU logiciel ») ; tout le reste est maison.

## Utilisation

```bash
pip install -r requirements.txt   # + ffmpeg ; libegl1 sous Linux
python render.py puce_atomique --stills 10,30,45     # images fixes de contrôle
python render.py puce_atomique --preview             # aperçu 960x540 à 30 i/s
python render.py puce_atomique                       # master 1080p60
python tools/timing.py intro echelle                 # minutage des répliques et des mots
```

## Vidéo 1 : « Au cœur du silicium » (`videos/puce_atomique/`) — en cours

Durée ≈ 7 min 11 s, 11 scènes, voix off complète générée (57 répliques).

- [x] Script de la voix off (`script.py`)
- [x] 00 Ouverture : appareil → puce → milliards d'interrupteurs → titre
- [~] 01 L'échelle : boîtier 3D → plan de la puce → cœur → cellules → transistors 3D → atomes
  - à faire : capot plus métallique, transition vers la vue de dessus, forêt de transistors (caméra plus éloignée,
    grilles découpées pour le tri de profondeur), coupe de l'aileron (réseau atomique + grille enveloppante)
- [ ] 02 Le silicium · 03 Le dopage · 04 Le transistor · 05 Le voyage d'un électron · 06 La logique
- [ ] 07 L'horloge · 08 La chaleur · 09 La frontière quantique · 10 Finale
- [ ] Sound design procédural, mixage, mastering (-14 LUFS)
- [ ] Rendu final 1080p60
