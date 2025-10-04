# Camera View Generation Fix - Implementation Summary

## Problème résolu / Problem Solved

Les caméras dans cv_minecraft ne généraient pas une vue depuis leur propre cube, mais enregistraient parfois la vue du propriétaire ou d'un autre contexte, et le résultat n'était pas toujours sauvegardé dans le dossier dédié à la caméra.

Cameras in cv_minecraft were not generating views from their own cube but were sometimes recording the owner's view or another context, and the result was not always saved in the camera-dedicated folder.

## Solution implémentée / Implemented Solution

### 1. CubeWindow - Référence au Cube / Cube Reference

**Fichier / File**: `protocol.py`

**Changements / Changes**:
- Ajout du paramètre `cube_ref` à `CubeWindow.__init__()` pour stocker une référence au cube parent
- Le CubeWindow peut maintenant accéder à la position et rotation du cube caméra via `self.cube_ref.position` et `self.cube_ref.rotation`

**Code**:
```python
def __init__(self, cube_id: str, width: int = 800, height: int = 600, 
             visible: bool = False, cube_ref: Optional['Cube'] = None):
    # ...
    self.cube_ref = cube_ref  # Store reference to parent cube
```

### 2. Rendu de Scène - Position et Rotation de la Caméra / Scene Rendering - Camera Position & Rotation

**Fichier / File**: `protocol.py`

**Changements / Changes**:
- Modification de `_render_simple_scene()` pour appliquer la position et rotation du cube caméra aux matrices OpenGL
- Application de la rotation (yaw et pitch) avant la translation
- Ajout de logs pour diagnostiquer la source de la vue

**Code**:
```python
def _render_simple_scene(self):
    # ...
    if self.cube_ref:
        # Apply camera's rotation (vertical then horizontal)
        h_rot, v_rot = self.cube_ref.rotation
        glRotatef(-v_rot, 1, 0, 0)  # Vertical rotation (pitch)
        glRotatef(-h_rot, 0, 1, 0)  # Horizontal rotation (yaw)
        
        # Apply camera position (negate to move world opposite of camera)
        cx, cy, cz = self.cube_ref.position
        glTranslatef(-cx, -cy, -cz - 5)  # -5 to move back from camera
        
        print(f"🎥 Rendering from camera position {self.cube_ref.position} with rotation {self.cube_ref.rotation}")
```

### 3. Sauvegarde dans le Dossier Caméra / Saving in Camera Directory

**Fichier / File**: `generate_camera_screenshot.py`

**Changements / Changes**:
- Extraction du `camera_id` depuis les données de vue
- Création automatique du dossier `recordings/{camera_id}/` 
- Génération d'un nom de fichier avec timestamp pour éviter les écrasements
- Logs pour indiquer où le screenshot est sauvegardé

**Code**:
```python
# Extract the actual camera_id used
actual_camera_id = view_data["camera"]["block_id"]

# Determine output path - save in recordings/{camera_id}/ directory
if output_image == "screenshot.png":
    camera_dir = f"recordings/{actual_camera_id}"
    os.makedirs(camera_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_image = os.path.join(camera_dir, f"screenshot_{timestamp}.png")
    print(f"💾 Output will be saved to camera directory: {output_image}")
```

### 4. Logs de Diagnostic / Diagnostic Logs

**Fichiers modifiés / Modified files**:
- `protocol.py`: Logs dans `take_screenshot()` et `_render_simple_scene()`
- `camera_view_query.py`: Logs pour afficher le camera_id utilisé
- `camera_view_reconstruction.py`: Logs pour afficher la position et rotation de la caméra
- `minecraft_client_fr.py`: Logs dans `GameRecorder.start_recording()` pour le dossier d'enregistrement
- `server.py`: Logs dans `get_blocks_in_view()` pour la source de la vue

**Exemples de logs / Log examples**:
```
📸 Taking screenshot from camera cube: camera_0
   Position: (100, 50, 75)
   Rotation: (45, -15)
🎥 Rendering from camera position (100, 50, 75) with rotation (45, -15)
✅ Screenshot captured successfully from camera camera_0

📷 Using camera: camera_0
💾 Output will be saved to camera directory: recordings/camera_0/screenshot_20251004_184206.png
📁 Screenshot saved in camera directory: recordings/camera_0/screenshot_20251004_184206.png
```

## Tests / Testing

### Tests Unitaires / Unit Tests

**Fichier / File**: `tests/test_camera_view_fix.py`

Tests que:
- Le CubeWindow reçoit et stocke correctement la référence au cube
- Les cubes normaux ne créent pas de fenêtre
- Les mises à jour de position/rotation sont accessibles via la fenêtre
- La logique de création de dossiers de screenshots fonctionne

### Tests d'Intégration / Integration Tests

**Fichier / File**: `tests/test_camera_view_integration.py`

Tests que:
- La reconstruction de vue utilise la position de la caméra depuis les données
- Les screenshots sont sauvegardés dans `recordings/{camera_id}/`
- Les informations de caméra sont correctement extraites
- Les logs fournissent des informations diagnostiques

### Exécution des Tests / Running Tests

```bash
# Tests unitaires / Unit tests
python3 tests/test_camera_view_fix.py

# Tests d'intégration / Integration tests
python3 tests/test_camera_view_integration.py
```

Tous les tests passent avec succès ✅

## Workflow de Capture / Capture Workflow

### 1. Via generate_camera_screenshot.py

```bash
# Générer un screenshot depuis la première caméra disponible
python3 generate_camera_screenshot.py

# Générer depuis une caméra spécifique
python3 generate_camera_screenshot.py --camera-id camera_0

# Avec rotation personnalisée
python3 generate_camera_screenshot.py --camera-id camera_0 --rotation 45 -10
```

**Résultat / Result**:
- Screenshot sauvegardé dans `recordings/{camera_id}/screenshot_YYYYMMDD_HHMMSS.png`
- Logs indiquant la position et rotation de la caméra utilisée

### 2. Via camera_view_query.py + camera_view_reconstruction.py

```bash
# Étape 1: Requête des données
python3 camera_view_query.py --camera-id camera_0 --output cam0_data.json

# Étape 2: Génération du screenshot
python3 camera_view_reconstruction.py --input cam0_data.json --output cam0_screenshot.png
```

### 3. Enregistrement depuis le Client / Recording from Client

Dans le client Minecraft (`minecraft_client_fr.py`):
- Placer une caméra avec le bloc caméra (touche `5`)
- Appuyer sur `F1` pour démarrer/arrêter l'enregistrement de la caméra 0
- Les frames sont sauvegardées dans `recordings/{camera_id}/session_YYYYMMDD_HHMMSS/`

## Vérification / Verification

Pour vérifier que les changements fonctionnent:

1. **Vérifier la référence cube**: Le `CubeWindow` a accès à `cube_ref.position` et `cube_ref.rotation`
2. **Vérifier le rendu**: Les logs montrent "Rendering from camera position X with rotation Y"
3. **Vérifier la sauvegarde**: Les screenshots sont dans `recordings/{camera_id}/`
4. **Vérifier les logs**: Tous les logs montrent le bon `camera_id` et la bonne position

## Fichiers Modifiés / Modified Files

- `protocol.py`: CubeWindow reçoit cube_ref, applique position/rotation, logs
- `camera_view_query.py`: Logs pour camera_id
- `camera_view_reconstruction.py`: Logs pour position/rotation  
- `generate_camera_screenshot.py`: Sauvegarde dans recordings/{camera_id}/
- `minecraft_client_fr.py`: Logs pour dossier d'enregistrement
- `server.py`: Logs pour get_blocks_in_view
- `tests/test_camera_view_fix.py`: Nouveaux tests unitaires
- `tests/test_camera_view_integration.py`: Nouveaux tests d'intégration

## Impact / Impact

✅ **Minimal**: Les changements sont chirurgicaux et n'affectent que le système de caméra
✅ **Rétrocompatible**: Les anciennes fonctionnalités continuent de fonctionner
✅ **Testé**: Tous les tests passent avec succès
✅ **Documenté**: Logs détaillés pour le diagnostic
✅ **Objectif atteint**: Les caméras génèrent maintenant une vue depuis leur propre position/rotation et sauvegardent dans le bon dossier
