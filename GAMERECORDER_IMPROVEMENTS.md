# Améliorations de Performance du GameRecorder

## Résumé des changements

Le système `GameRecorder` a été amélioré pour offrir de meilleures performances lors de la capture de frames du gameplay Minecraft/Pyglet.

## Problème résolu

L'ancienne implémentation enregistrait chaque frame directement sur le disque en format PNG dans la boucle principale du jeu, ce qui causait:
- Blocage de la boucle principale pendant l'encodage PNG et l'écriture disque
- Limitations de performance I/O disque
- Compression PNG lente
- Baisse potentielle du FPS du jeu pendant l'enregistrement

## Solution implémentée

### Architecture à thread dédié

La nouvelle implémentation utilise une architecture à deux threads:

1. **Thread principal (Pyglet)**: 
   - Capture rapide du buffer Pyglet
   - Extraction des données brutes RGBA en mémoire
   - Ajout des données dans une queue mémoire
   - Retour immédiat à la boucle de jeu (non-bloquant)

2. **Thread d'écriture dédié**:
   - Traite la queue de frames de manière asynchrone
   - Convertit les données RGBA en RGB
   - Encode en JPEG (quality=85) - plus rapide que PNG
   - Écrit sur le disque sans bloquer le jeu

### Caractéristiques techniques

- **Queue mémoire**: Utilise `collections.deque` pour stocker temporairement les frames
- **Encodage JPEG**: Qualité 85, plus rapide que PNG et fichiers plus petits
- **Thread daemon**: Le thread d'écriture est un daemon pour éviter de bloquer la fermeture
- **Arrêt propre**: La méthode `stop()` attend que toutes les frames soient écrites (timeout 30s)
- **Gestion d'erreurs**: Exceptions capturées pour éviter de crasher le jeu

## Modifications apportées

### Classe GameRecorder

#### Nouveaux attributs
- `frame_queue`: Queue pour stocker les frames avant écriture
- `writer_thread`: Référence au thread d'écriture
- `writer_running`: Flag pour contrôler le thread

#### Nouvelles méthodes
- `_writer_worker()`: Worker du thread d'écriture (privé)
- `stop()`: Alias pour `stop_recording()` (nouvelle API)

#### Méthodes modifiées
- `__init__()`: Initialise la queue et les variables de thread
- `start_recording()`: Démarre le thread d'écriture
- `stop_recording()`: Arrête proprement le thread d'écriture
- `capture_frame()`: Extrait les données brutes et les met en queue au lieu d'écrire directement

### Format de sortie

Les frames sont maintenant enregistrées en **JPEG** (`.jpg`) au lieu de PNG (`.png`):
- Fichiers plus petits (~10x plus petits)
- Encodage plus rapide
- Qualité 85 (excellent compromis qualité/taille)
- Optimisation activée

## Compatibilité

### API publique préservée

Toutes les méthodes et attributs publics existants sont conservés:
- `GameRecorder(output_dir)` - constructeur
- `start_recording()` - démarre l'enregistrement
- `stop_recording()` - arrête l'enregistrement
- `capture_frame(window)` - capture une frame
- `set_fps(fps)` - définit le FPS
- `session_dir` - répertoire de session
- `frame_count` - compteur de frames
- `is_recording` - statut d'enregistrement

### Nouvelle API

- `stop()` - alias pour `stop_recording()`, méthode plus intuitive

### Changements visibles

1. **Format de fichier**: `.jpg` au lieu de `.png`
   - Les scripts de conversion vidéo devront être adaptés
   - Fichiers beaucoup plus petits

2. **Message lors de l'arrêt**: 
   - Nouveau message "⏳ Attente de l'écriture des frames restantes..." pendant la finalisation

## Tests

Nouveaux tests ajoutés dans `test_threaded_recorder.py`:
- Test de création et arrêt du thread
- Test de gestion de la queue
- Test de la méthode `stop()`
- Test du format JPEG
- Test de compatibilité API

Tous les tests existants dans `test_game_recorder.py` continuent de fonctionner.

## Performance attendue

### Avant
- Écriture PNG synchrone: ~50-100ms par frame
- Blocage de la boucle principale
- Limitation à ~10-20 FPS max pour l'enregistrement

### Après
- Capture buffer: ~1-2ms par frame
- Pas de blocage de la boucle principale
- Enregistrement possible à 60+ FPS
- Écriture JPEG asynchrone en arrière-plan

## Utilisation

```python
from minecraft_client_fr import GameRecorder

# Initialisation (identique)
recorder = GameRecorder(output_dir="recordings")
recorder.set_fps(60)  # FPS plus élevé possible maintenant

# Démarrage (identique)
session_dir = recorder.start_recording()

# Dans la boucle de jeu (identique)
while running:
    render_frame()
    if recording:
        recorder.capture_frame(window)  # Non-bloquant maintenant!

# Arrêt (nouvelle méthode disponible)
recorder.stop()  # ou recorder.stop_recording()
```

## Dépendances

- `PIL/Pillow` (déjà dans requirements.txt) - requis pour l'encodage JPEG
- `threading` (standard library)
- `collections.deque` (standard library)

## Migration

Pour les utilisateurs existants, aucune modification de code n'est nécessaire. Le seul changement visible est:

1. Les frames sont en `.jpg` au lieu de `.png`
2. Pour la conversion vidéo avec ffmpeg:

```bash
# Ancien (PNG)
ffmpeg -framerate 30 -pattern_type glob -i 'frame_*.png' -c:v libx264 output.mp4

# Nouveau (JPEG)
ffmpeg -framerate 30 -pattern_type glob -i 'frame_*.jpg' -c:v libx264 output.mp4
```

## Notes techniques

### Thread safety
- La queue (`deque`) est thread-safe pour append/popleft
- Pas de verrous nécessaires pour les opérations de base
- Les attributs de contrôle (`is_recording`, `writer_running`) sont atomiques

### Gestion mémoire
- Les données brutes sont copiées hors du buffer Pyglet immédiatement
- La queue ne devrait pas grossir excessivement car l'écriture JPEG est rapide
- Si la queue grossit trop, c'est un indicateur que le disque est trop lent

### Robustesse
- Le thread est daemon pour éviter de bloquer la fermeture du programme
- Timeout de 30s sur le join pour éviter un blocage infini
- Gestion d'erreurs complète pour éviter les crashs

## Conclusion

Ces améliorations permettent:
- ✅ Capture à débit élevé (60+ FPS)
- ✅ Pas de blocage de la boucle de jeu
- ✅ Fichiers plus petits (JPEG vs PNG)
- ✅ Encodage plus rapide
- ✅ Compatibilité API préservée
- ✅ Arrêt propre avec finalisation automatique
