# Guide Rapide : Enregistrement de Gameplay

## 🎬 Démarrage en 3 Étapes

### 1. Lancer le Client
```bash
python3 minecraft_client_fr.py
```

### 2. Jouer et Enregistrer
- Jouez normalement au jeu
- Appuyez sur **F9** pour démarrer l'enregistrement
- Un message "🎬 Enregistrement démarré" s'affiche
- Appuyez sur **F3** pour voir l'indicateur 🔴 REC

### 3. Arrêter et Récupérer
- Appuyez sur **F9** pour arrêter
- Vos frames sont dans `recordings/session_YYYYMMDD_HHMMSS/`

## 📹 Convertir en Vidéo

```bash
cd recordings/session_YYYYMMDD_HHMMSS/
ffmpeg -framerate 30 -pattern_type glob -i 'frame_*.png' \
  -c:v libx264 -pix_fmt yuv420p ma_video.mp4
```

## 🎯 Contrôles Essentiels

| Touche | Action |
|--------|--------|
| **F9** | Démarrer/Arrêter l'enregistrement |
| **F3** | Afficher les infos (voir statut REC) |

## 📚 Documentation Complète

- **Guide détaillé** : [GAMEPLAY_RECORDING.md](GAMEPLAY_RECORDING.md)
- **Détails techniques** : [IMPLEMENTATION_RECORDING.md](IMPLEMENTATION_RECORDING.md)
- **Client français** : [CLIENT_FRANCAIS.md](CLIENT_FRANCAIS.md)

## 🧪 Tester

```bash
# Tests unitaires
python3 test_game_recorder.py

# Démonstration interactive
python3 demo_recording.py
```

## ✅ C'est Fait!

Le système utilise exactement le code demandé :
```python
buffer = pyglet.image.get_buffer_manager().get_color_buffer()
```

Et fonctionne en parallèle pendant que vous jouez! 🎮
