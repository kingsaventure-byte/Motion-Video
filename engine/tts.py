"""Voix off via Edge TTS (voix neuronales Microsoft), avec horodatage mot par mot.

- Format 24 kHz / 96 kbit/s (2x le débit par défaut de la librairie).
- Cache par empreinte (voix, débit, hauteur, texte) : seules les répliques modifiées
  sont régénérées.
"""
import asyncio
import json
import os
import ssl

import aiohttp
import edge_tts
import edge_tts.communicate as _comm

_CA = '/root/.ccr/ca-bundle.crt'
if os.path.exists(_CA):  # proxy TLS de l'environnement cloud
    _comm._SSL_CTX = ssl.create_default_context(cafile=_CA)

_FORMAT = 'audio-24khz-96kbitrate-mono-mp3'
_orig_send = aiohttp.ClientWebSocketResponse.send_str


async def _send_str(self, data, *a, **k):
    return await _orig_send(self, data.replace('audio-24khz-48kbitrate-mono-mp3', _FORMAT), *a, **k)


aiohttp.ClientWebSocketResponse.send_str = _send_str


async def _synth(text, voice, rate, pitch, path):
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary='WordBoundary')
    audio = bytearray()
    words = []
    async for ch in com.stream():
        if ch['type'] == 'audio':
            audio += ch['data']
        elif ch['type'] == 'WordBoundary':
            s = ch['offset'] / 1e7
            words.append((ch['text'], s, s + ch['duration'] / 1e7))
    with open(path, 'wb') as f:
        f.write(audio)
    return words


def _duration(path):
    import subprocess
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def synthesize(lines, voice, rate, pitch, out_dir):
    """Génère (ou réutilise) l'audio de chaque réplique. Renvoie le manifeste."""
    os.makedirs(out_dir, exist_ok=True)
    man_path = os.path.join(out_dir, 'manifest.json')
    manifest = {}
    if os.path.exists(man_path):
        with open(man_path) as f:
            manifest = json.load(f)
    todo = []
    for ln in lines:
        k = ln.key(voice, rate, pitch)
        mp3 = os.path.join(out_dir, f'{k}.mp3')
        if k in manifest and os.path.exists(mp3) and os.path.getsize(mp3) > 0:
            continue
        todo.append((k, ln, mp3))

    async def run():
        for i, (k, ln, mp3) in enumerate(todo):
            for attempt in range(5):
                try:
                    words = await _synth(ln.text, voice, rate, pitch, mp3)
                    break
                except Exception as e:  # réseau capricieux : on réessaie
                    if attempt == 4:
                        raise
                    print(f'  [tts] nouvel essai ({e.__class__.__name__})')
                    await asyncio.sleep(2 ** attempt)
            manifest[k] = {'file': mp3, 'dur': _duration(mp3), 'words': words, 'text': ln.text}
            print(f'  [tts] {i + 1}/{len(todo)}  {ln.id}: {manifest[k]["dur"]:.2f}s')
            with open(man_path, 'w') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=1)

    if todo:
        asyncio.run(run())
    return manifest
