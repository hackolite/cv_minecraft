# Camera Screenshot System

## Vue d'ensemble / Overview

Ce système permet de requêter les données de vue d'une caméra via WebSocket en utilisant son `block_id`, puis de reconstruire la vue côté client pour générer un screenshot.png.

This system allows querying camera view data via WebSocket using its `block_id`, then reconstructing the view client-side to generate a screenshot.png.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Serveur Minecraft / Minecraft Server                      │
│  - Caméras avec block_id (camera_0, camera_1, etc.)       │
│  - API WebSocket pour requêtes par block_id               │
└─────────────────────────────────────────────────────────────┘
                           ↓ WebSocket Query
┌─────────────────────────────────────────────────────────────┐
│  camera_view_query.py                                       │
│  - Se connecte au serveur                                   │
│  - Requête les blocs visibles depuis la caméra            │
│  - Sauvegarde les données en JSON                          │
└─────────────────────────────────────────────────────────────┘
                           ↓ JSON Data
┌─────────────────────────────────────────────────────────────┐
│  camera_view_reconstruction.py                              │
│  - Charge les données JSON                                  │
│  - Projette les blocs 3D vers 2D                           │
│  - Génère screenshot.png                                    │
└─────────────────────────────────────────────────────────────┘
```

## Scripts

### 1. `camera_view_query.py`

Requête les données de vue d'une caméra via WebSocket.

**Usage:**
```bash
# Requête depuis la première caméra disponible
python3 camera_view_query.py

# Requête depuis une caméra spécifique
python3 camera_view_query.py --camera-id camera_0

# Avec rotation et distance de vue personnalisées
python3 camera_view_query.py --rotation 45 -10 --view-distance 30

# Sortie vers un fichier personnalisé
python3 camera_view_query.py --output my_view_data.json
```

**Options:**
- `--server URI`: URI du serveur WebSocket (défaut: ws://localhost:8765)
- `--camera-id ID`: block_id de la caméra spécifique (défaut: première disponible)
- `--rotation H V`: Rotation de la caméra en degrés (horizontal vertical)
- `--view-distance D`: Distance de vue (défaut: 50.0)
- `--output FILE`: Fichier JSON de sortie (défaut: camera_view_data.json)

**Sortie:**
Fichier JSON contenant:
- Informations de la caméra (position, rotation, block_id)
- Liste de tous les blocs visibles avec leurs propriétés
- Métadonnées de la requête

### 2. `camera_view_reconstruction.py`

Reconstruit la vue depuis les données JSON et génère un screenshot.

**Usage:**
```bash
# Générer screenshot depuis camera_view_data.json
python3 camera_view_reconstruction.py

# Depuis un fichier personnalisé
python3 camera_view_reconstruction.py --input my_view_data.json

# Avec dimensions personnalisées
python3 camera_view_reconstruction.py --width 1920 --height 1080

# Sortie vers un fichier personnalisé
python3 camera_view_reconstruction.py --output my_screenshot.png
```

**Options:**
- `--input FILE`: Fichier JSON d'entrée (défaut: camera_view_data.json)
- `--output FILE`: Fichier screenshot de sortie (défaut: screenshot.png)
- `--width W`: Largeur de l'image en pixels (défaut: 800)
- `--height H`: Hauteur de l'image en pixels (défaut: 600)
- `--fov F`: Champ de vision en degrés (défaut: 70.0)

### 3. `generate_camera_screenshot.py`

Script tout-en-un qui combine requête et reconstruction.

**Usage:**
```bash
# Générer screenshot depuis la première caméra
python3 generate_camera_screenshot.py

# Depuis une caméra spécifique
python3 generate_camera_screenshot.py --camera-id camera_0

# Avec options personnalisées
python3 generate_camera_screenshot.py \
  --camera-id camera_0 \
  --rotation 45 -10 \
  --view-distance 30 \
  --output my_screenshot.png \
  --width 1920 \
  --height 1080

# Garder le fichier JSON intermédiaire
python3 generate_camera_screenshot.py --keep-json
```

**Options:** Combine toutes les options des deux scripts précédents.

## Exemples d'utilisation / Usage Examples

### Workflow complet / Complete Workflow

```bash
# 1. Démarrer le serveur
python3 server.py

# 2. (Dans un autre terminal) Générer un screenshot
python3 generate_camera_screenshot.py --camera-id camera_0 --output camera0_view.png
```

### Workflow en deux étapes / Two-Step Workflow

```bash
# 1. Requête des données
python3 camera_view_query.py --camera-id camera_0 --output cam0_data.json

# 2. Génération du screenshot
python3 camera_view_reconstruction.py --input cam0_data.json --output cam0_screenshot.png
```

### Utilisation avancée / Advanced Usage

```bash
# Capturer plusieurs vues avec différentes rotations
for angle in 0 45 90 135 180; do
  python3 generate_camera_screenshot.py \
    --camera-id camera_0 \
    --rotation $angle 0 \
    --output "camera0_view_${angle}.png"
done

# Générer un screenshot haute résolution
python3 generate_camera_screenshot.py \
  --width 1920 \
  --height 1080 \
  --fov 90 \
  --output hd_screenshot.png
```

## Format des données / Data Format

### Fichier JSON de vue / View Data JSON File

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
    },
    {
      "position": [71, 100, 66],
      "block_type": "stone",
      "block_id": null,
      "collision": true,
      "distance": 15.2
    }
  ],
  "metadata": {
    "total_blocks": 2,
    "query_timestamp": 1234567890.123
  }
}
```

## Rendu / Rendering

Le script de reconstruction utilise:
- Projection 3D vers 2D avec perspective
- Couleurs par type de bloc
- Luminosité basée sur la distance
- Tri par profondeur pour l'occlusion

The reconstruction script uses:
- 3D to 2D perspective projection
- Colors by block type
- Distance-based brightness
- Depth sorting for occlusion

### Couleurs des blocs / Block Colors

| Type    | Couleur / Color       | RGB           |
|---------|-----------------------|---------------|
| grass   | Forest green          | (34, 139, 34) |
| sand    | Wheat                 | (238, 214, 175) |
| brick   | Firebrick            | (178, 34, 34) |
| stone   | Gray                  | (128, 128, 128) |
| wood    | Saddle brown          | (139, 69, 19) |
| leaf    | Green                 | (0, 128, 0)   |
| water   | Dodger blue           | (64, 164, 223) |
| camera  | Magenta               | (255, 0, 255) |
| user    | Yellow                | (255, 255, 0) |

## Intégration avec le système existant / Integration with Existing System

Ces scripts utilisent l'infrastructure existante:
- API WebSocket du serveur (`server.py`)
- Système de block_id (`BLOCK_METADATA_SYSTEM.md`)
- Messages de protocole (`protocol.py`)

These scripts use existing infrastructure:
- Server WebSocket API (`server.py`)
- Block_id system (`BLOCK_METADATA_SYSTEM.md`)
- Protocol messages (`protocol.py`)

## Dépendances / Dependencies

- `websockets`: Communication WebSocket
- `Pillow` (PIL): Génération d'images
- `asyncio`: Async/await pour WebSocket

Déjà dans `requirements.txt` / Already in `requirements.txt`

## Extension future / Future Extensions

- Support pour plusieurs caméras simultanément
- Animation (séquence de screenshots)
- Rendu 3D plus avancé avec textures
- Export vidéo
- Mode temps réel avec mise à jour continue

- Support for multiple cameras simultaneously
- Animation (sequence of screenshots)
- More advanced 3D rendering with textures
- Video export
- Real-time mode with continuous updates

## Voir aussi / See Also

- `BLOCK_METADATA_SYSTEM.md`: Documentation du système block_id
- `example_block_id_query.py`: Exemple de requête par block_id
- `test_block_id_integration.py`: Tests d'intégration
