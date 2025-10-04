# Système de Capture d'Écran de Caméra - Résumé

## Vue d'ensemble

Ce système permet de requêter les données de vue d'une caméra via WebSocket en utilisant son `block_id`, puis de reconstruire la vue côté client pour générer un fichier `screenshot.png`.

## Architecture

Le système est composé de trois scripts principaux qui travaillent ensemble :

### 1. `camera_view_query.py` - Requête des données
Connecte au serveur via WebSocket et récupère les blocs visibles depuis une caméra.

**Fonctionnement :**
- Se connecte au serveur Minecraft (WebSocket)
- Récupère la liste des caméras disponibles avec leurs `block_id`
- Envoie une requête `get_blocks_list` avec :
  - `query_type: "view"`
  - `block_id`: ID de la caméra (ex: "camera_0")
  - `rotation`: Direction de vue [horizontal, vertical]
  - `view_distance`: Distance de vue
- Sauvegarde les données au format JSON

**Exemple de requête WebSocket :**
```json
{
  "type": "get_blocks_list",
  "data": {
    "query_type": "view",
    "block_id": "camera_0",
    "rotation": [0, 0],
    "view_distance": 50.0
  }
}
```

### 2. `camera_view_reconstruction.py` - Reconstruction côté client
Charge les données JSON et génère un screenshot PNG.

**Fonctionnement :**
- Charge le fichier JSON avec les données de vue
- Projette chaque bloc 3D vers des coordonnées 2D (projection perspective)
- Applique la luminosité basée sur la distance
- Trie les blocs par profondeur (pour l'occlusion)
- Rend l'image avec PIL/Pillow
- Sauvegarde en `screenshot.png`

**Caractéristiques du rendu :**
- Projection 3D → 2D avec perspective
- Couleurs par type de bloc
- Luminosité basée sur la distance
- Tri par profondeur pour gérer l'occlusion
- Overlay d'informations (position, rotation, etc.)

### 3. `generate_camera_screenshot.py` - Workflow complet
Script tout-en-un qui combine les deux opérations.

## Utilisation

### Méthode Simple (Recommandée)

```bash
# Screenshot depuis la première caméra disponible
python3 generate_camera_screenshot.py

# Screenshot depuis une caméra spécifique
python3 generate_camera_screenshot.py --camera-id camera_0

# Avec options personnalisées
python3 generate_camera_screenshot.py \
  --camera-id camera_0 \
  --rotation 45 -15 \
  --view-distance 30 \
  --output mon_screenshot.png \
  --width 1920 --height 1080
```

### Méthode en Deux Étapes

```bash
# Étape 1: Requête des données
python3 camera_view_query.py --camera-id camera_0 --output vue_camera.json

# Étape 2: Génération du screenshot
python3 camera_view_reconstruction.py --input vue_camera.json --output screenshot.png
```

## Format des Données

### Fichier JSON (vue_camera.json)

```json
{
  "camera": {
    "block_id": "camera_0",
    "position": [69, 102, 64],
    "rotation": [0, 0],
    "view_distance": 50.0
  },
  "blocks": [
    {
      "position": [70, 100, 65],
      "block_type": "grass",
      "block_id": null,
      "collision": true,
      "distance": 10.5
    }
  ],
  "metadata": {
    "total_blocks": 150,
    "query_timestamp": 1234567890.123
  }
}
```

## Tests et Démos

### Test Complet
```bash
python3 tests/test_camera_screenshot_system.py
```

Ce test vérifie :
- La connexion au serveur
- Les requêtes par `block_id`
- Les différentes rotations
- Le format des données
- La comparaison block_id vs position

### Démo avec Multiples Screenshots
```bash
python3 tests/demo_camera_screenshots.py
```

Génère :
- Screenshots depuis différentes caméras
- Screenshots avec différentes rotations
- Screenshot haute résolution (1920x1080)
- Exemple avec conservation du JSON

## Options Disponibles

### camera_view_query.py
- `--server URI`: URI du serveur WebSocket (défaut: ws://localhost:8765)
- `--camera-id ID`: ID de la caméra (défaut: première disponible)
- `--rotation H V`: Rotation horizontale et verticale en degrés
- `--view-distance D`: Distance de vue (défaut: 50.0)
- `--output FILE`: Fichier JSON de sortie

### camera_view_reconstruction.py
- `--input FILE`: Fichier JSON d'entrée
- `--output FILE`: Fichier PNG de sortie (défaut: screenshot.png)
- `--width W`: Largeur de l'image (défaut: 800)
- `--height H`: Hauteur de l'image (défaut: 600)
- `--fov F`: Champ de vision en degrés (défaut: 70.0)

### generate_camera_screenshot.py
Combine toutes les options ci-dessus plus :
- `--keep-json`: Conserver le fichier JSON intermédiaire

## Avantages de cette Architecture

1. **Séparation des préoccupations**
   - Requête de données (serveur)
   - Reconstruction de vue (client)

2. **Flexibilité**
   - Peut requêter depuis n'importe quelle caméra par son `block_id`
   - Rotation et distance de vue configurables
   - Résolution d'image personnalisable

3. **Réutilisabilité**
   - Les données JSON peuvent être réutilisées
   - Génération de multiples vues depuis les mêmes données
   - Possibilité d'archiver les vues

4. **Performance**
   - Reconstruction côté client (pas de charge serveur)
   - Format JSON efficace pour le transfert
   - Pas besoin de rendu 3D serveur

5. **Extension facile**
   - Ajout de nouveaux types de requêtes
   - Amélioration du rendu (textures, ombres, etc.)
   - Export vers d'autres formats

## Intégration avec le Système Existant

Ce système utilise l'infrastructure existante :

- **server.py** : API WebSocket pour les requêtes
- **BLOCK_METADATA_SYSTEM.md** : Système de `block_id`
- **protocol.py** : Messages de protocole
- **example_block_id_query.py** : Exemples de requêtes

Aucune modification du serveur n'a été nécessaire - tout fonctionne avec les API existantes.

## Extensions Futures Possibles

1. **Multi-caméras**
   - Capture simultanée depuis plusieurs caméras
   - Comparaison de vues côte à côte

2. **Animation**
   - Séquence de screenshots
   - Export en GIF ou vidéo

3. **Rendu Avancé**
   - Textures réelles des blocs
   - Ombres et éclairage
   - Anti-aliasing

4. **Mode Temps Réel**
   - Mise à jour continue
   - Stream de screenshots

5. **Interface Web**
   - Visualisation dans le navigateur
   - Contrôle interactif de la caméra

## Dépendances

Toutes les dépendances sont déjà dans `requirements.txt` :
- `websockets` : Communication WebSocket
- `Pillow` : Génération d'images PNG
- `asyncio` : Programmation asynchrone

## Conclusion

Ce système implémente une solution complète pour :
- ✅ Requêter avec WebSocket par `block_id`
- ✅ Spécifiquement pour les caméras (extensible à d'autres blocs)
- ✅ Renvoyer les données nécessaires
- ✅ Reconstruction côté client
- ✅ Génération de `screenshot.png`

Le code est organisé, testé, documenté et prêt à l'emploi.
