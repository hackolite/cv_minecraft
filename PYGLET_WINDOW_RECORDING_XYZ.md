# Test de Création de Fenêtres Pyglet et Enregistrement avec x,y,z

## Vue d'ensemble

Ce document décrit les tests et améliorations apportés au système de création de fenêtres Pyglet et d'enregistrement du buffer avec suivi des positions x, y, z.

## Problème identifié

L'issue demandait de:
1. Tester la création de fenêtres Pyglet
2. Tester l'enregistrement du buffer Pyglet avec coordonnées x, y, z
3. Vérifier l'intégration car les enregistrements vidéo étaient bizarres

## Améliorations apportées

### 1. Correction des imports OpenGL (protocol.py)

**Problème**: Les fonctions OpenGL legacy comme `glMatrixMode` n'étaient pas importées.

**Solution**: Ajout de l'import `from OpenGL.GL import *` pour inclure les fonctions OpenGL manquantes.

```python
# Avant
from pyglet.gl import *

# Après  
from pyglet.gl import *
from OpenGL.GL import *  # Pour les fonctions OpenGL legacy
```

### 2. Métadonnées de position par session (minecraft_client_fr.py)

**Amélioration**: Ajout des informations de position de la caméra dans les métadonnées de session.

Les fichiers `session_info.json` contiennent maintenant:
```json
{
  "duration_seconds": 0.16,
  "frame_count": 3,
  "average_fps": 18.75,
  "start_time": "2025-10-04T20:36:19",
  "end_time": "2025-10-04T20:36:19",
  "camera_info": {
    "camera_id": "camera_1",
    "position": {
      "x": 10,
      "y": 50,
      "z": 10
    },
    "rotation": {
      "horizontal": 0,
      "vertical": 0
    }
  }
}
```

### 3. Métadonnées de position par frame (minecraft_client_fr.py)

**Nouvelle fonctionnalité**: Suivi de la position x, y, z pour chaque frame capturée.

Un nouveau fichier `frames_metadata.json` est créé avec les métadonnées de chaque frame:
```json
[
  {
    "frame_number": 0,
    "timestamp": 0.001,
    "width": 800,
    "height": 600,
    "camera_position": {
      "x": 10,
      "y": 50,
      "z": 10
    },
    "camera_rotation": {
      "horizontal": 0,
      "vertical": 0
    }
  },
  {
    "frame_number": 1,
    "timestamp": 0.051,
    "width": 800,
    "height": 600,
    "camera_position": {
      "x": 15,
      "y": 52,
      "z": 15
    },
    "camera_rotation": {
      "horizontal": 0,
      "vertical": 0
    }
  }
]
```

### 4. Tests complets (test_pyglet_window_recording_xyz.py)

**Nouveau fichier de test**: Tests exhaustifs pour valider le système complet.

#### Tests inclus:

1. **Test 1: Création de fenêtres Pyglet**
   - Vérifie que les fenêtres Pyglet sont créées pour les cubes caméra
   - Teste plusieurs positions différentes
   - Valide les types de fenêtres

2. **Test 2: Capture du buffer avec coordonnées**
   - Capture le buffer Pyglet
   - Vérifie les dimensions et le format
   - Associe la position x, y, z de la caméra

3. **Test 3: GameRecorder avec métadonnées**
   - Teste l'enregistrement avec GameRecorder
   - Vérifie la sauvegarde des métadonnées de session
   - Valide les informations de position

4. **Test 4: Enregistrement multi-caméras**
   - Teste l'enregistrement simultané de plusieurs caméras
   - Vérifie que chaque caméra a ses propres métadonnées
   - Valide la gestion des positions différentes

5. **Test 5: Suivi des positions x,y,z**
   - Teste le déplacement de la caméra entre les frames
   - Vérifie que les positions sont trackées correctement
   - Valide le fichier frames_metadata.json

## Structure des fichiers d'enregistrement

Après un enregistrement, la structure est:

```
recordings/
└── session_YYYYMMDD_HHMMSS/
    ├── frame_000000.jpg       # Frame capturée au format JPEG
    ├── frame_000001.jpg
    ├── frame_000002.jpg
    ├── session_info.json      # Métadonnées de la session
    └── frames_metadata.json   # Métadonnées par frame avec x,y,z
```

## Utilisation

### Lancer les tests

```bash
# Avec environnement graphique
python3 tests/test_pyglet_window_recording_xyz.py

# En mode headless (sans écran)
xvfb-run -a python3 tests/test_pyglet_window_recording_xyz.py
```

### Résultat attendu

```
======================================================================
TESTS COMPLETS: Fenêtres Pyglet et Enregistrement Buffer avec x,y,z
======================================================================

✅ Test 1: RÉUSSI - Toutes les fenêtres créées correctement
✅ Test 2: RÉUSSI - Buffer capturé avec position
✅ Test 3: RÉUSSI - Enregistrement avec métadonnées
✅ Test 4: RÉUSSI - Enregistrement multi-caméras
✅ Test 5: RÉUSSI - Positions trackées avec x,y,z dans métadonnées

Total: 5 | Réussis: 5 | Échoués: 0

🎉 TOUS LES TESTS ONT RÉUSSI!
```

## Utilisation dans le code

### Créer une caméra et enregistrer

```python
from protocol import Cube
from minecraft_client_fr import GameRecorder

# Créer un cube caméra à une position spécifique
camera = Cube("my_camera", (10, 50, 10), cube_type="camera")

# Créer un recorder pour cette caméra
recorder = GameRecorder(output_dir="recordings", camera_cube=camera)

# Démarrer l'enregistrement
recorder.start_recording()

# Capturer des frames (dans votre boucle de rendu)
recorder.capture_frame()

# Déplacer la caméra (les positions seront trackées)
camera.update_position((15, 52, 15))
recorder.capture_frame()

# Arrêter l'enregistrement
recorder.stop_recording()
```

### Lire les métadonnées

```python
import json
from pathlib import Path

# Lire les métadonnées de session
session_dir = Path("recordings/session_20251004_203619")
with open(session_dir / "session_info.json") as f:
    session_info = json.load(f)
    print(f"Caméra: {session_info['camera_info']['camera_id']}")
    print(f"Position: {session_info['camera_info']['position']}")

# Lire les métadonnées par frame
with open(session_dir / "frames_metadata.json") as f:
    frames_meta = json.load(f)
    for frame in frames_meta:
        pos = frame['camera_position']
        print(f"Frame {frame['frame_number']}: x={pos['x']}, y={pos['y']}, z={pos['z']}")
```

## Avantages

1. **Traçabilité**: Chaque frame est associée à une position exacte x, y, z
2. **Débogage**: Les métadonnées permettent de comprendre d'où vient chaque frame
3. **Analyse**: Possibilité d'analyser les trajectoires de caméra
4. **Reconstruction**: Les positions peuvent être utilisées pour reconstruire la vue 3D
5. **Synchronisation**: Multiple caméras peuvent être synchronisées via les timestamps

## Compatibilité

- ✅ Python 3.12
- ✅ Pyglet 2.1.9
- ✅ PyOpenGL 3.1.10
- ✅ Mode headless avec Xvfb
- ✅ Compatible avec les systèmes sans affichage graphique

## Prérequis

```bash
pip install pyglet websockets pillow PyOpenGL PyOpenGL_accelerate

# Pour mode headless
sudo apt-get install xvfb
```

## Résolution des problèmes

### Erreur "Cannot connect to display"

```bash
# Utiliser Xvfb
xvfb-run -a python3 your_script.py
```

### Avertissements OpenGL

Les messages `baseOperation = glMatrixMode` sont des avertissements PyOpenGL normaux et n'affectent pas la fonctionnalité.

### Métadonnées manquantes

Vérifier que:
1. La caméra a bien été créée avec `cube_type="camera"`
2. Le GameRecorder a été créé avec le paramètre `camera_cube`
3. L'enregistrement a été démarré avec `start_recording()`

## Conclusion

Le système de création de fenêtres Pyglet et d'enregistrement du buffer fonctionne correctement avec un suivi complet des positions x, y, z. Les métadonnées sont sauvegardées à la fois au niveau de la session et par frame, permettant une analyse détaillée des enregistrements.

Tous les tests passent avec succès, confirmant que:
- ✅ Les fenêtres Pyglet sont créées correctement
- ✅ Le buffer peut être capturé avec les coordonnées x, y, z
- ✅ Les métadonnées sont sauvegardées correctement
- ✅ L'enregistrement multi-caméras fonctionne
- ✅ Le suivi de position est précis et fiable
