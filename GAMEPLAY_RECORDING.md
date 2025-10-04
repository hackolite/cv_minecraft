# Système d'Enregistrement de Gameplay

## Vue d'ensemble

Le client Minecraft français (`minecraft_client_fr.py`) intègre désormais un système d'enregistrement de gameplay qui capture les frames en temps réel pendant que vous jouez.

## Fonctionnalités

- **Capture en temps réel** : Utilise `pyglet.image.get_buffer_manager().get_color_buffer()` pour capturer le buffer de la fenêtre
- **Enregistrement parallèle** : Thread dédié pour l'écriture disque sans bloquer la boucle de jeu
- **Haute performance** : Queue mémoire et encodage JPEG asynchrone pour capture à 60+ FPS
- **Sessions organisées** : Chaque enregistrement est sauvegardé dans un répertoire dédié avec timestamp
- **FPS configurable** : Par défaut à 30 FPS, ajustable jusqu'à 60+ FPS
- **Format optimisé** : Encodage JPEG (qualité 85) pour fichiers plus petits et écriture plus rapide
- **Indicateur visuel** : Affichage du statut d'enregistrement dans l'interface de debug

## Utilisation

### Démarrer/Arrêter l'enregistrement

**Touche : F9**

Appuyez sur **F9** pour démarrer ou arrêter l'enregistrement. Un message s'affichera à l'écran pour confirmer l'action.

### Contrôles clavier

| Touche | Action |
|--------|--------|
| **F9** | Démarrer/Arrêter l'enregistrement |
| **F3** | Afficher/Masquer les informations de debug (inclut le statut d'enregistrement) |

### Indicateurs visuels

Lorsque l'enregistrement est actif :
- Un message "🎬 Enregistrement démarré" apparaît
- Dans l'interface de debug (F3), vous verrez "🔴 REC (X frames)" où X est le nombre de frames capturées
- À l'arrêt, un résumé s'affiche avec la durée et le nombre de frames

## Structure des fichiers

Les enregistrements sont sauvegardés dans le répertoire `recordings/` à la racine du projet :

```
recordings/
├── session_20231204_143022/
│   ├── frame_000000.jpg
│   ├── frame_000001.jpg
│   ├── frame_000002.jpg
│   ├── ...
│   └── session_info.json
└── session_20231204_145530/
    ├── frame_000000.jpg
    ├── ...
    └── session_info.json
```

### Format des fichiers

- **Frames** : Images JPEG numérotées séquentiellement (`frame_XXXXXX.jpg`)
  - Format : JPEG avec qualité 85
  - Optimisation activée pour réduire la taille
  - ~10x plus petites que PNG, encodage plus rapide
- **session_info.json** : Métadonnées de la session
  ```json
  {
    "duration_seconds": 120.5,
    "frame_count": 3615,
    "average_fps": 30.0,
    "start_time": "2023-12-04T14:30:22",
    "end_time": "2023-12-04T14:32:22"
  }
  ```

## Conversion en vidéo

Pour convertir les frames en vidéo, utilisez ffmpeg :

```bash
# Depuis le répertoire de session
cd recordings/session_YYYYMMDD_HHMMSS/

# Conversion en MP4 (30 FPS)
ffmpeg -framerate 30 -pattern_type glob -i 'frame_*.jpg' \
  -c:v libx264 -pix_fmt yuv420p output.mp4

# Conversion en WebM
ffmpeg -framerate 30 -pattern_type glob -i 'frame_*.jpg' \
  -c:v libvpx-vp9 -pix_fmt yuv420p output.webm

# Conversion en GIF (optimisé)
ffmpeg -framerate 30 -pattern_type glob -i 'frame_*.jpg' \
  -vf "fps=15,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  output.gif
```

## Configuration avancée

### Modifier le FPS d'enregistrement

Dans le code (`minecraft_client_fr.py`), vous pouvez ajuster le FPS dans la méthode `__init__` de `GameRecorder` :

```python
# Dans GameRecorder.__init__
self.capture_interval = 1.0 / 30.0  # 30 FPS par défaut
```

Ou programmatiquement après création :

```python
# Exemple pour 60 FPS
window.recorder.set_fps(60)
```

### Changer le répertoire de sortie

Modifiez le paramètre lors de l'initialisation dans `MinecraftWindow.__init__` :

```python
self.recorder = GameRecorder(output_dir="mes_enregistrements")
```

## Performance

### Impact sur les performances
### Impact sur les performances

- **Capture** : Très légère (~1-2ms par frame, non-bloquant)
- **Queue mémoire** : Thread dédié pour écriture asynchrone
- **Encodage JPEG** : Plus rapide que PNG, fichiers ~10x plus petits
- **FPS du jeu** : Aucun impact, la boucle principale n'est jamais bloquée
- **Mémoire** : Minimal, les frames sont rapidement écrites depuis la queue

### Optimisation

Pour réduire l'espace disque et améliorer les performances :
1. Les frames sont déjà en JPEG optimisé (qualité 85)
2. Diminuer le FPS si nécessaire (15-20 FPS au lieu de 30)
3. Convertir en vidéo compressée après l'enregistrement
4. Supprimer les frames JPEG une fois converties en vidéo

## Dépannage

### L'enregistrement ne démarre pas

**Cause** : Pyglet n'est pas disponible ou erreur de contexte OpenGL

**Solution** :
```bash
# Vérifier l'installation de Pyglet
pip install pyglet==1.5.27

# Vérifier les dépendances OpenGL
sudo apt-get install libglu1-mesa libglu1-mesa-dev
```

### Message "⚠️ Enregistrement non disponible"

**Cause** : Le client tourne en mode dégradé sans Pyglet

**Solution** : Assurez-vous d'avoir un environnement graphique ou Xvfb configuré :
```bash
# Avec Xvfb
xvfb-run python3 minecraft_client_fr.py
```

### Les frames ne sont pas capturées

**Cause** : L'intervalle de capture est trop court ou la fenêtre n'est pas rendue

**Solution** : Vérifiez que le jeu tourne normalement et que `on_draw()` est appelé

### Erreur "Erreur capture frame"

**Cause** : Problème avec le buffer manager de Pyglet

**Solution** : 
1. Vérifiez que la version de Pyglet est 1.5.27
2. Assurez-vous que le contexte OpenGL est correctement initialisé
3. Vérifiez les permissions d'écriture dans le répertoire `recordings/`

## Exemples d'utilisation

### Scénario 1 : Enregistrer une construction

1. Lancez le client : `python3 minecraft_client_fr.py`
2. Commencez votre construction
3. Appuyez sur **F9** pour démarrer l'enregistrement
4. Construisez votre structure
5. Appuyez sur **F9** pour arrêter
6. Convertissez en vidéo avec ffmpeg

### Scénario 2 : Créer un tutoriel

1. Démarrez le client et activez le mode debug avec **F3**
2. Lancez l'enregistrement avec **F9**
3. Effectuez les actions que vous voulez montrer
4. Arrêtez l'enregistrement
5. Utilisez les frames pour créer un GIF animé ou une vidéo

### Scénario 3 : Capture de bugs

1. Jouez normalement
2. Dès qu'un bug apparaît, appuyez sur **F9**
3. Reproduisez le bug pendant l'enregistrement
4. Arrêtez l'enregistrement
5. Partagez les frames ou la vidéo pour analyse

## Intégration avec d'autres outils

### Montage vidéo

Les frames JPEG peuvent être importées dans n'importe quel logiciel de montage :
- **DaVinci Resolve** : Importez la séquence d'images
- **Adobe Premiere** : Import > Media Browser > Séquence d'images
- **OpenShot** : Ajoutez les frames comme séquence

### Streaming

Pour le streaming en direct, vous pouvez :
1. Enregistrer avec le GameRecorder
2. Utiliser OBS pour capturer la fenêtre directement
3. Combiner les deux pour avoir un backup

## Notes techniques

### Implémentation

Le système utilise :
- Architecture à deux threads pour performance maximale
- Thread principal : capture rapide du buffer Pyglet (~1-2ms)
- Thread dédié : encodage JPEG et écriture asynchrone
- Queue mémoire (`collections.deque`) pour communication entre threads
- `pyglet.image.get_buffer_manager().get_color_buffer()` pour la capture
- `PIL/Pillow` pour l'encodage JPEG optimisé (qualité 85)
- Arrêt propre avec finalisation automatique des frames restantes

### Limitations

- Format de sortie : JPEG uniquement (conversion vidéo via ffmpeg)
- FPS maximum : 60+ FPS possible grâce au threading
- Pas de capture audio (jeu sans son actuellement)
- Nécessite PIL/Pillow pour l'encodage JPEG

## Roadmap

Améliorations futures possibles :
- [x] Threading pour haute performance
- [x] Encodage JPEG pour fichiers plus petits
- [ ] Capture directe en vidéo (H.264)
- [ ] Interface graphique pour gérer les enregistrements
- [ ] Marqueurs temporels (bookmarks)
- [ ] Support de différents codecs
- [ ] Capture audio si implémenté

## Support

Pour toute question ou problème :
1. Vérifiez cette documentation
2. Consultez les logs du client
3. Testez avec `test_game_recorder.py`
4. Ouvrez une issue sur GitHub

## Licence

Ce système fait partie du projet cv_minecraft et suit la même licence.
