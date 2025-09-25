# Système de Caméras Minecraft - Documentation

## Vue d'ensemble

Le système de caméras permet de créer automatiquement des utilisateurs avec serveurs FastAPI individuels lorsque des blocs caméra (rouges) sont placés dans le monde Minecraft. Chaque caméra offre un endpoint FastAPI pour visualiser ce qu'elle voit, comme un utilisateur normal.

## Fonctionnalités

### ✅ Bloc Caméra Spécial
- **Nouveau type de bloc**: `CAMERA` (couleur rouge)
- **Ajouté à l'inventaire**: Disponible via la touche 5
- **Placement automatique**: Place le bloc et crée automatiquement l'utilisateur caméra

### ✅ Création Automatique d'Utilisateurs
- **Utilisateur par caméra**: Chaque bloc caméra crée un `MinecraftClient` dédié
- **Position intelligente**: L'utilisateur se positionne un bloc au-dessus de la caméra
- **Serveur FastAPI individuel**: Port unique pour chaque caméra (8081+)
- **Mode headless**: Fonctionne sans interface graphique

### ✅ API REST pour Chaque Caméra
- **Endpoint de vue**: `/get_view` - Capture d'écran de ce que voit la caméra
- **API complète**: Tous les endpoints standard du `MinecraftClient`
- **Documentation**: Swagger UI disponible sur `http://localhost:<port>/docs`

### ✅ Script de Visualisation
- **`camera_viewer.py`**: Script pour récupérer et afficher les vues des caméras
- **Listing**: `--list` pour voir toutes les caméras actives
- **Visualisation**: `--camera <id>` ou `--position x y z`
- **Sauvegarde**: `--save <filename.png>` pour sauvegarder les images

## Installation et Usage

### 1. Prérequis

```bash
# Installer les dépendances
pip install -r requirements.txt
```

### 2. Démarrage du Serveur

```bash
# Démarrer le serveur Minecraft
python3 server.py
```

### 3. Connexion d'un Client

```bash
# Client avec interface graphique
python3 minecraft_client_fr.py

# Ou client abstrait avec API
python3 demo_minecraft_client.py --gui
```

### 4. Placement de Caméras

1. **Sélectionner le bloc caméra**: Appuyez sur `5` pour sélectionner le bloc `CAMERA`
2. **Placer la caméra**: Clic droit pour placer le bloc rouge là où vous voulez la caméra
3. **Caméra créée automatiquement**: Un utilisateur avec serveur FastAPI est créé automatiquement

### 5. Visualisation des Caméras

```bash
# Lister toutes les caméras actives
python3 camera_viewer.py --list

# Visualiser une caméra par son ID
python3 camera_viewer.py --camera Camera_50_60_50

# Visualiser une caméra par sa position
python3 camera_viewer.py --position 50 60 50

# Sauvegarder la vue d'une caméra
python3 camera_viewer.py --camera Camera_50_60_50 --save ma_vue.png
```

## Architecture Technique

### Fichiers Clés

- **`protocol.py`**: Ajout du type de bloc `CAMERA`
- **`camera_user_manager.py`**: Gestionnaire des utilisateurs caméra
- **`server.py`**: Détection des blocs caméra et création d'utilisateurs
- **`minecraft_client.py`**: Client abstrait utilisé pour les caméras
- **`camera_viewer.py`**: Script de visualisation des caméras

### Flux de Fonctionnement

1. **Placement du bloc**: Joueur place un bloc `CAMERA` dans le monde
2. **Détection serveur**: Le serveur détecte le placement via `_handle_block_place`
3. **Création utilisateur**: `camera_manager.create_camera_user()` crée un `MinecraftClient`
4. **Serveur FastAPI**: Chaque caméra démarre son propre serveur sur un port unique
5. **Visualisation**: `camera_viewer.py` interroge l'endpoint `/get_view` de la caméra

### Gestion des Ports

- **Port de base**: 8081 (8080 souvent utilisé par le client principal)
- **Allocation automatique**: Ports suivants (8082, 8083, etc.) si occupés
- **Libération**: Ports libérés lors de la suppression des caméras

## API des Caméras

Chaque caméra expose une API FastAPI complète :

### Endpoints Principaux

```bash
# Page d'accueil de l'API
GET http://localhost:8081/

# Capture d'écran de la caméra (PRINCIPAL)
GET http://localhost:8081/get_view

# Statut de la caméra
GET http://localhost:8081/status

# Documentation interactive
GET http://localhost:8081/docs
```

### Endpoints de Contrôle

```bash
# Déplacer la caméra
POST http://localhost:8081/move?dx=5&dy=0&dz=0

# Téléporter la caméra
POST http://localhost:8081/teleport?x=100&y=70&z=100

# Placer un bloc depuis la caméra
POST http://localhost:8081/place_block?x=101&y=70&z=100&block_type=STONE
```

## Exemples d'Utilisation

### Script Python pour Récupérer une Vue

```python
import requests
from camera_user_manager import camera_manager

# Lister les caméras
cameras = camera_manager.get_cameras()
if cameras:
    camera = cameras[0]
    
    # Récupérer la vue
    response = requests.get(camera['view_endpoint'])
    if response.status_code == 200:
        with open('camera_view.png', 'wb') as f:
            f.write(response.content)
        print("Vue sauvegardée!")
```

### Intégration avec des Scripts IA

```python
# Exemple d'utilisation pour une IA
def get_camera_view(camera_id):
    """Récupère la vue d'une caméra pour analyse IA."""
    cameras = camera_manager.get_cameras()
    
    for camera in cameras:
        if camera['id'] == camera_id:
            response = requests.get(camera['view_endpoint'])
            if response.status_code == 200:
                return response.content  # Image PNG raw
    return None

# Utilisation
view_data = get_camera_view("Camera_50_60_50")
if view_data:
    # Traiter l'image avec OpenCV, PIL, etc.
    pass
```

## Tests et Démonstrations

### Tests Unitaires

```bash
# Tests des blocs caméra
python3 test_camera_blocks.py

# Tests d'intégration
python3 test_camera_integration.py
```

### Démonstrations

```bash
# Démo complète du système
python3 demo_camera_usage.py

# Démo avec serveur et client (plus complexe)
python3 demo_camera_system.py
```

## Dépannage

### Problèmes Courants

1. **Caméra ne se crée pas**
   - Vérifiez que le serveur Minecraft fonctionne
   - Vérifiez les logs pour les erreurs de création

2. **Port déjà utilisé**
   - Le système trouve automatiquement des ports libres
   - Vérifiez qu'aucun autre service n'utilise les ports 8081+

3. **Vue non accessible**
   - Attendez quelques secondes que le serveur FastAPI démarre
   - Vérifiez que la caméra apparaît dans `--list`

4. **Mode headless**
   - Les caméras fonctionnent automatiquement en mode headless
   - Pas besoin d'affichage graphique

### Logs et Debug

```bash
# Activer les logs détaillés
export PYTHONPATH=/home/runner/work/cv_minecraft/cv_minecraft
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from camera_user_manager import camera_manager
# Vos tests ici
"
```

## Contribution

Le système de caméras est conçu pour être extensible :

1. **Nouveaux types de caméras**: Modifier `CameraUser` pour des fonctionnalités spéciales
2. **Endpoints personnalisés**: Ajouter des routes dans `MinecraftClient`
3. **Visualiseurs avancés**: Étendre `camera_viewer.py` pour de nouvelles fonctionnalités

## Licence

Même licence que le projet principal cv_minecraft.