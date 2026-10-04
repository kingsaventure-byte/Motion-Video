"""Moteur de rendu motion design maison.

Architecture :
  ease / anim   -> courbes d'animation, tweens, springs, keyframes
  noise         -> bruit cohérent déterministe (mouvements organiques)
  color         -> palette et mélanges de couleurs
  fonts / text  -> typographie (HarfBuzz pour le crénage, Skia pour la rasterisation)
  painter       -> canevas double tampon : image principale + tampon d'émission (halo)
  camera        -> caméra 2D et projection 3D perspective
  post          -> post-traitement : bloom, aberration chromatique, vignette, grain, tone mapping
  timeline      -> scènes, répliques, synchro mot par mot avec la voix off
  render        -> rendu multiprocessus, encodage ffmpeg
  tts / audio   -> voix off Edge TTS, synthèse sonore procédurale, mixage, mastering
"""
