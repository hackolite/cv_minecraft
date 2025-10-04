# Quick Reference - Camera Screenshot System
# Guide Rapide - Système de Capture d'Écran de Caméra

## Quick Start / Démarrage Rapide

### EN: Generate a screenshot from a camera
### FR: Générer un screenshot depuis une caméra

```bash
# Start the server first / Démarrer le serveur d'abord
python3 server.py

# In another terminal / Dans un autre terminal
python3 generate_camera_screenshot.py
```

## Common Commands / Commandes Courantes

### EN: List available cameras
### FR: Lister les caméras disponibles

```bash
python3 camera_view_query.py --camera-id camera_0 --keep-json
# Then check camera_view_data.json
```

### EN: Specific camera with rotation
### FR: Caméra spécifique avec rotation

```bash
python3 generate_camera_screenshot.py \
  --camera-id camera_0 \
  --rotation 45 -15 \
  --output my_view.png
```

### EN: High resolution screenshot
### FR: Screenshot haute résolution

```bash
python3 generate_camera_screenshot.py \
  --width 1920 \
  --height 1080 \
  --fov 90 \
  --output hd_screenshot.png
```

### EN: Multiple cameras
### FR: Plusieurs caméras

```bash
for cam in camera_0 camera_1 camera_2; do
  python3 generate_camera_screenshot.py \
    --camera-id $cam \
    --output ${cam}_view.png
done
```

## Parameters / Paramètres

| Option | EN Description | FR Description | Default / Défaut |
|--------|----------------|----------------|------------------|
| `--camera-id` | Camera block ID | ID du bloc caméra | First available / Première disponible |
| `--rotation H V` | Horizontal, Vertical angles | Angles horizontal, vertical | 0 0 |
| `--view-distance` | View range in blocks | Distance de vue en blocs | 50.0 |
| `--output` | Output PNG file | Fichier PNG de sortie | screenshot.png |
| `--width` | Image width (pixels) | Largeur image (pixels) | 800 |
| `--height` | Image height (pixels) | Hauteur image (pixels) | 600 |
| `--fov` | Field of view (degrees) | Champ de vision (degrés) | 70.0 |
| `--keep-json` | Keep intermediate JSON | Garder le JSON intermédiaire | false |

## Rotation Guide / Guide de Rotation

```
Horizontal (H):
  0°   = North / Nord
  90°  = East / Est
  180° = South / Sud
  270° = West / Ouest

Vertical (V):
  -90° = Straight down / Tout en bas
  -45° = Looking down / Regardant vers le bas
  0°   = Horizontal / Horizontal
  45°  = Looking up / Regardant vers le haut
  90°  = Straight up / Tout en haut
```

## Examples / Exemples

### EN: Panorama (360° views)
### FR: Panorama (vues 360°)

```bash
for angle in 0 45 90 135 180 225 270 315; do
  python3 generate_camera_screenshot.py \
    --camera-id camera_0 \
    --rotation $angle 0 \
    --output panorama_${angle}.png
done
```

### EN: Vertical sweep
### FR: Balayage vertical

```bash
for angle in -90 -45 0 45 90; do
  python3 generate_camera_screenshot.py \
    --camera-id camera_0 \
    --rotation 0 $angle \
    --output vertical_${angle}.png
done
```

## Files Created / Fichiers Créés

| File / Fichier | Purpose / But |
|----------------|---------------|
| `screenshot.png` | Final image / Image finale |
| `camera_view_data.json` | Intermediate data (if --keep-json) / Données intermédiaires |
| `demo_screenshots/*.png` | Demo outputs / Sorties de démo |

## Testing / Tests

```bash
# Test the complete system / Tester le système complet
python3 test_camera_screenshot_system.py

# Generate demo screenshots / Générer des screenshots de démo
python3 demo_camera_screenshots.py
```

## Troubleshooting / Dépannage

### EN: Server not running
### FR: Serveur non démarré

```
Error: [Errno 111] Connection refused
Solution: Start server with `python3 server.py`
```

### EN: No cameras found
### FR: Aucune caméra trouvée

```
Error: No cameras available
Solution: Check server logs - cameras should be created at startup
```

### EN: Message too big
### FR: Message trop grand

```
Error: message too big
Solution: Reduce --view-distance (e.g., --view-distance 30)
```

### EN: No blocks visible in screenshot
### FR: Aucun bloc visible dans le screenshot

```
Issue: Screenshot is mostly sky
Solution: 
- Try different rotations (e.g., --rotation 0 -45)
- Increase --view-distance
- The cameras are positioned high up, so may only see each other
```

## API Reference / Référence API

### EN: WebSocket Query Format
### FR: Format de Requête WebSocket

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

### EN: Response Format
### FR: Format de Réponse

```json
{
  "type": "blocks_list",
  "data": {
    "blocks": [
      {
        "position": [x, y, z],
        "block_type": "grass",
        "block_id": null,
        "collision": true,
        "distance": 10.5
      }
    ]
  }
}
```

## Documentation / Documentation

- **CAMERA_SCREENSHOT_SYSTEM.md** - Full documentation (EN/FR)
- **CAMERA_SYSTEM_SUMMARY_FR.md** - Detailed summary (FR)
- **BLOCK_METADATA_SYSTEM.md** - Block ID system reference
- **example_block_id_query.py** - Example code

## Scripts Overview / Vue d'ensemble des Scripts

| Script | EN Purpose | FR But |
|--------|-----------|--------|
| `camera_view_query.py` | Query camera data | Requêter données caméra |
| `camera_view_reconstruction.py` | Render screenshot | Rendre screenshot |
| `generate_camera_screenshot.py` | Complete workflow | Workflow complet |
| `test_camera_screenshot_system.py` | System tests | Tests système |
| `demo_camera_screenshots.py` | Generate demos | Générer démos |
