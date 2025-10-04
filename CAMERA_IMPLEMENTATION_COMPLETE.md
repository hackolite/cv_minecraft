# Camera Screenshot System - Implementation Complete

## Summary / Résumé

**EN:** Complete implementation of a camera screenshot generation system that queries camera view data via WebSocket using `block_id` and reconstructs the view client-side to generate a `screenshot.png`.

**FR:** Implémentation complète d'un système de génération de screenshots de caméra qui requête les données de vue via WebSocket en utilisant le `block_id` et reconstruit la vue côté client pour générer un `screenshot.png`.

## Problem Statement / Énoncé du Problème

**FR (Original):**
> organise le code, ou rajoute script si nécessaire pour requêter avec websocket par block_id, spécifiquement pour la caméra pour le moment, mais pas seulement, renvoit les données nécessaires pour reconstruire la vue de la caméra sous forme d'un screenshot.png, la reconstruction se fait coté client.

**EN (Translation):**
> Organize the code or add a script if necessary to query via websocket by block_id, specifically for the camera for now (but not only), return the necessary data to reconstruct the camera view as a screenshot.png, the reconstruction is done client-side.

## Solution / Solution

### ✅ What Was Implemented

1. **Camera View Query Script** (`camera_view_query.py`)
   - Queries camera view data via WebSocket using `block_id`
   - Connects to server and retrieves camera list
   - Queries blocks visible from camera perspective
   - Saves data to JSON format for client-side reconstruction

2. **Client-Side Reconstruction** (`camera_view_reconstruction.py`)
   - Loads camera view data from JSON
   - Performs 3D to 2D projection with perspective
   - Renders blocks with colors and distance-based brightness
   - Generates `screenshot.png` file

3. **Combined Workflow Script** (`generate_camera_screenshot.py`)
   - All-in-one convenience script
   - Combines query and reconstruction in single command
   - Provides comprehensive options for customization

4. **Test Suite** (`test_camera_screenshot_system.py`)
   - Comprehensive tests for the complete workflow
   - Validates WebSocket queries
   - Tests different rotations and view distances
   - Verifies data format

5. **Demo Script** (`demo_camera_screenshots.py`)
   - Generates multiple example screenshots
   - Demonstrates different camera perspectives
   - Shows various configuration options

## Files Created / Fichiers Créés

### Scripts
- `camera_view_query.py` - Query camera view data via WebSocket
- `camera_view_reconstruction.py` - Reconstruct view and generate screenshot
- `generate_camera_screenshot.py` - Complete workflow (recommended)
- `test_camera_screenshot_system.py` - Comprehensive test suite
- `demo_camera_screenshots.py` - Demo with multiple examples

### Documentation
- `CAMERA_SCREENSHOT_SYSTEM.md` - Complete system documentation (EN/FR)
- `CAMERA_SYSTEM_SUMMARY_FR.md` - Detailed French summary
- `CAMERA_QUICK_REFERENCE.md` - Quick reference guide (EN/FR)
- `CAMERA_IMPLEMENTATION_COMPLETE.md` - This file

## Quick Start / Démarrage Rapide

### Prerequisites / Prérequis

```bash
# Install dependencies / Installer les dépendances
pip install websockets Pillow

# Start the server / Démarrer le serveur
python3 server.py
```

### Basic Usage / Utilisation de Base

```bash
# Generate screenshot from first available camera
# Générer un screenshot depuis la première caméra
python3 generate_camera_screenshot.py

# From specific camera with custom options
# Depuis une caméra spécifique avec options personnalisées
python3 generate_camera_screenshot.py \
  --camera-id camera_0 \
  --rotation 45 -15 \
  --view-distance 30 \
  --output my_screenshot.png \
  --width 1920 --height 1080
```

### Testing / Tests

```bash
# Run comprehensive tests / Exécuter les tests complets
python3 test_camera_screenshot_system.py

# Generate demo screenshots / Générer des screenshots de démo
python3 demo_camera_screenshots.py
```

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Minecraft Server (server.py)                    │
│  ┌────────────────────────────────────────────┐  │
│  │  WebSocket API                             │  │
│  │  - get_cameras_list → cameras with IDs    │  │
│  │  - get_blocks_list (by block_id)          │  │
│  └────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────┘
                     │
                     │ WebSocket
                     │ { type: "get_blocks_list",
                     │   data: { block_id: "camera_0" }}
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│  Client: camera_view_query.py                    │
│  ┌────────────────────────────────────────────┐  │
│  │  1. Connect to server                      │  │
│  │  2. Get cameras list                       │  │
│  │  3. Query blocks from camera perspective   │  │
│  │  4. Save to JSON                           │  │
│  └────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────┘
                     │
                     │ camera_view_data.json
                     │ { camera: {...}, blocks: [...] }
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│  Client: camera_view_reconstruction.py           │
│  ┌────────────────────────────────────────────┐  │
│  │  1. Load JSON data                         │  │
│  │  2. Project 3D blocks to 2D                │  │
│  │  3. Apply colors and brightness            │  │
│  │  4. Render with PIL/Pillow                 │  │
│  │  5. Save as screenshot.png                 │  │
│  └────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
              screenshot.png
```

## Key Features / Fonctionnalités Clés

### ✅ Block ID Query Support
- Query camera views using `block_id` instead of explicit coordinates
- Works with any block that has a `block_id` (cameras, users, etc.)
- Extensible to other block types

### ✅ Client-Side Reconstruction
- All rendering done client-side (no server load)
- Flexible image size and quality
- Customizable field of view and projection

### ✅ Flexible Configuration
- Configurable camera rotation (horizontal, vertical)
- Adjustable view distance
- Custom output resolution
- Various export options

### ✅ Complete Workflow
- Single command for complete operation
- Or separate query/reconstruction for advanced use
- JSON data can be reused/archived

## Technical Details / Détails Techniques

### WebSocket Query Format

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

### Response Format

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

### Rendering Pipeline

1. **Load Data**: Read JSON with camera info and blocks
2. **Transform**: Apply camera rotation to each block
3. **Project**: 3D → 2D perspective projection
4. **Depth Sort**: Sort blocks by distance for proper occlusion
5. **Render**: Draw blocks with colors and brightness
6. **Export**: Save as PNG file

## Integration with Existing System / Intégration

This implementation uses **existing server infrastructure**:
- ✅ WebSocket API from `server.py`
- ✅ Block ID system from `BLOCK_METADATA_SYSTEM.md`
- ✅ Protocol messages from `protocol.py`
- ✅ No server modifications required

## Examples / Exemples

### Example 1: Basic Screenshot
```bash
python3 generate_camera_screenshot.py
# Output: screenshot.png (800x600)
```

### Example 2: Specific Camera, Custom View
```bash
python3 generate_camera_screenshot.py \
  --camera-id camera_0 \
  --rotation 90 -30 \
  --view-distance 40
```

### Example 3: High Resolution
```bash
python3 generate_camera_screenshot.py \
  --width 1920 \
  --height 1080 \
  --fov 90
```

### Example 4: Panorama Generation
```bash
for angle in 0 45 90 135 180 225 270 315; do
  python3 generate_camera_screenshot.py \
    --rotation $angle 0 \
    --output "panorama_${angle}.png"
done
```

## Documentation Reference / Référence Documentation

| Document | Purpose |
|----------|---------|
| `CAMERA_SCREENSHOT_SYSTEM.md` | Complete technical documentation |
| `CAMERA_SYSTEM_SUMMARY_FR.md` | Detailed French summary with architecture |
| `CAMERA_QUICK_REFERENCE.md` | Quick reference for common tasks |
| `BLOCK_METADATA_SYSTEM.md` | Block ID system documentation |

## Testing Results / Résultats des Tests

✅ All tests pass successfully:
- Connection to server via WebSocket
- Camera list retrieval with block_ids
- Block queries using block_id
- Different rotation angles
- Data format validation
- Position vs block_id query comparison

✅ Demo generates multiple screenshots:
- Default view from camera_0
- Rotated views (90°, 180°, etc.)
- Looking down view
- High resolution (1920x1080)
- With JSON data preservation

## Future Enhancements / Améliorations Futures

Possible extensions (not implemented yet):

1. **Real-time streaming**: Continuous screenshot updates
2. **Video export**: Convert screenshot sequences to video
3. **Advanced rendering**: Textures, shadows, lighting
4. **Multi-camera**: Simultaneous capture from multiple cameras
5. **Web interface**: Browser-based visualization
6. **3D reconstruction**: Full 3D scene reconstruction

## Conclusion

✅ **Requirements Met / Exigences Remplies:**

1. ✅ Organize code / add scripts for WebSocket queries by block_id
2. ✅ Specifically for cameras (but extensible to other blocks)
3. ✅ Return necessary data to reconstruct camera view
4. ✅ Generate screenshot.png
5. ✅ Reconstruction done client-side

**Status: Complete and Tested / Statut : Complet et Testé**

All scripts are functional, tested, and documented with examples.
Tous les scripts sont fonctionnels, testés et documentés avec des exemples.
