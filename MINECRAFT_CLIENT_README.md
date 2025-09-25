# Client Minecraft Abstrait avec API FastAPI

Cette implémentation fournit une classe `MinecraftClient` abstraite qui permet de contrôler un client Minecraft soit directement via l'interface graphique (pour les humains), soit programmatiquement via une API REST FastAPI.

## Fonctionnalités

✅ **Interface Graphique Complète**: Basée sur `minecraft_client_fr.py` avec toutes les fonctionnalités de jeu
✅ **API REST Intégrée**: Serveur FastAPI pour contrôle programmatique  
✅ **Mode Headless**: Fonctionnement sans interface graphique
✅ **Configuration Flexible**: Position, type de bloc, port API configurables
✅ **Capture d'Écran**: Endpoint pour voir ce que voit le joueur
✅ **Thread Séparé**: Le serveur API fonctionne en parallèle du client

## Installation

```bash
pip install -r requirements.txt
```

Dépendances principales:
- `pyglet==1.5.27` - Interface graphique 3D
- `fastapi>=0.104.0` - API REST
- `uvicorn>=0.24.0` - Serveur ASGI
- `Pillow>=8.0.0` - Traitement d'images
- `requests` - Pour les tests (optionnel)

## Usage Rapide

### 1. Mode GUI (Humain)

```python
from minecraft_client import MinecraftClient

# Créer un client avec interface graphique
client = MinecraftClient(
    position=(50, 80, 50),
    block_type="STONE",
    server_port=8080
)

# Démarrer le serveur API
client.start_server()

# Lancer le client (interface graphique + API)
client.run()
```

### 2. Mode Headless (Programmatique)

```python
from minecraft_client import MinecraftClient
import requests
import time

# Créer un client sans interface graphique
client = MinecraftClient(
    position=(100, 60, 100),
    enable_gui=False,
    server_port=8080
)

# Démarrer le serveur
client.start_server()

# Contrôler via API (dans un thread séparé)
def control_client():
    time.sleep(2)
    
    # Téléporter le joueur
    requests.post("http://localhost:8080/teleport", 
                 params={"x": 200, "y": 80, "z": 200})
    
    # Placer un bloc
    requests.post("http://localhost:8080/place_block",
                 params={"x": 201, "y": 80, "z": 200, "block_type": "BRICK"})

import threading
threading.Thread(target=control_client, daemon=True).start()

# Lancer le client headless
client.run()
```

### 3. Scripts de Démonstration

```bash
# Mode GUI avec API
python3 demo_minecraft_client.py --gui --port 8080

# Mode headless avec démonstration API
python3 demo_minecraft_client.py --headless --demo-api --port 8080

# Configuration personnalisée
python3 demo_minecraft_client.py --position 100 150 100 --block-type BRICK
```

## API REST Endpoints

Le serveur FastAPI expose les endpoints suivants:

### Informations

- **GET** `/` - Informations générales de l'API
- **GET** `/status` - Statut complet du client
- **GET** `/docs` - Documentation interactive Swagger

### Mouvement

- **POST** `/move?dx=X&dy=Y&dz=Z` - Mouvement relatif
- **POST** `/teleport?x=X&y=Y&z=Z` - Téléportation absolue

### Blocs

- **POST** `/place_block?x=X&y=Y&z=Z&block_type=TYPE` - Placer un bloc
- **POST** `/remove_block?x=X&y=Y&z=Z` - Supprimer un bloc

### Vue

- **GET** `/get_view` - Capture d'écran (PNG) de ce que voit le joueur

## Exemples d'Appels API

```bash
# Statut du client
curl http://localhost:8080/status

# Téléporter à une position
curl -X POST 'http://localhost:8080/teleport?x=100&y=50&z=100'

# Mouvement relatif
curl -X POST 'http://localhost:8080/move?dx=10&dy=5&dz=-5'

# Placer un bloc de pierre
curl -X POST 'http://localhost:8080/place_block?x=101&y=50&z=101&block_type=STONE'

# Supprimer un bloc
curl -X POST 'http://localhost:8080/remove_block?x=101&y=50&z=101'

# Capture d'écran
curl http://localhost:8080/get_view -o screenshot.png
```

## Configuration

### Paramètres du Constructeur

```python
MinecraftClient(
    position=(x, y, z),           # Position de départ (défaut: [30, 50, 80])
    block_type="GRASS",           # Type de bloc par défaut  
    server_host="localhost",       # Host du serveur API
    server_port=8080,             # Port du serveur API
    enable_gui=True               # Mode GUI (True) ou headless (False)
)
```

### Types de Blocs Supportés

- `"GRASS"` - Herbe (défaut)
- `"STONE"` - Pierre  
- `"SAND"` - Sable
- `"BRICK"` - Brique

## Contrôles GUI

Quand l'interface graphique est activée:

- **WASD** ou **ZQSD** : Se déplacer
- **Espace** : Sauter / Voler vers le haut
- **Shift** : S'accroupir / Voler vers le bas  
- **Clic droit** : Placer un bloc
- **Clic gauche** : Détruire un bloc
- **Tab** : Afficher/masquer les informations debug
- **F** : Activer/désactiver le vol
- **1-4** : Changer le type de bloc

## Architecture

```
MinecraftClient
├── Interface Graphique (Pyglet/OpenGL)
│   ├── Rendu 3D du monde
│   ├── Gestion des entrées utilisateur
│   └── Affichage UI/debug
│
└── Serveur API (FastAPI/Uvicorn)
    ├── Thread séparé
    ├── Endpoints REST
    └── Documentation automatique
```

## Gestion des Erreurs

- **Mode Headless**: Se lance automatiquement sans GUI si l'affichage n'est pas disponible
- **Port Occupé**: Le serveur indique si le port est déjà utilisé
- **Client Non Démarré**: Les endpoints retournent HTTP 400 si le client n'est pas actif
- **Blocs Invalides**: Validation des types de blocs dans l'API

## Intégration avec le Code Existant

Cette classe utilise et abstrait `minecraft_client_fr.py` en:

1. **Préservant** toute la logique de jeu existante
2. **Ajoutant** une couche API REST
3. **Permettant** le mode headless
4. **Supprimant** les dépendances aux observeurs (système de caméras externes)

## Exemples Avancés

Voir `example_usage.py` pour des exemples détaillés incluant:
- Usage basique avec GUI
- Contrôle programmatique headless  
- Mode mixte (GUI + API simultanés)

## Dépannage

### Problème d'Affichage
```
Warning: Display not available, GUI disabled
```
→ Le client passe automatiquement en mode headless

### Erreur de Port
```
ERROR: [Errno 98] address already in use
```
→ Utilisez un port différent avec `server_port=XXXX`

### Import Pyglet Échoue
```
ImportError: Library "GLU" not found
```
→ Installez: `sudo apt-get install libglu1-mesa-dev`

## Suppression du Système d'Observateurs

Cette implémentation **supprime complètement** l'ancien système d'observateurs externes (`observer_camera.py`, `fastapi_camera_server.py`, etc.) et le remplace par une approche unifiée où le client principal peut être contrôlé directement via API.

Les avantages:
- ✅ Plus simple à utiliser
- ✅ Moins de dépendances
- ✅ API plus cohérente
- ✅ Support natif headless/GUI