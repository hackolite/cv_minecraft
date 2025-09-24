# Système d'Utilisateurs RTSP - Documentation

## Vue d'ensemble

Ce système permet la création automatique d'utilisateurs au démarrage du serveur Minecraft, dont la vision est servie par des serveurs RTSP individuels. Chaque utilisateur RTSP représente une "caméra" virtuelle dans le monde Minecraft qui peut diffuser sa vision via RTSP.

## Fonctionnalités

### 1. Création Automatique d'Utilisateurs
- **3 utilisateurs RTSP** sont créés automatiquement au démarrage du serveur
- Configuration par défaut dans `users_config.json`
- Chaque utilisateur a une position et orientation unique dans le monde

### 2. Serveurs RTSP Intégrés
- **Serveur RTSP individuel** pour chaque utilisateur
- **Ports RTSP uniques**: 8554, 8555, 8556
- **URLs RTSP**: `rtsp://localhost:8554/stream`, etc.
- Streaming simulé de la vision de chaque utilisateur

### 3. Intégration Serveur
- Les utilisateurs RTSP apparaissent dans la liste des joueurs
- Distinction claire entre utilisateurs RTSP et clients connectés
- Support de la physique et des collisions pour les utilisateurs RTSP

## Configuration

### Fichier `users_config.json`

```json
{
    "users": [
        {
            "name": "Observateur_1",
            "rtsp_port": 8554,
            "position": [30, 50, 80],
            "rotation": [0, 0]
        },
        {
            "name": "Observateur_2", 
            "rtsp_port": 8555,
            "position": [50, 50, 60],
            "rotation": [90, 0]
        },
        {
            "name": "Observateur_3",
            "rtsp_port": 8556,
            "position": [70, 50, 40],
            "rotation": [180, 0]
        }
    ],
    "rtsp_settings": {
        "host": "localhost",
        "resolution": "1280x720",
        "fps": 30,
        "bitrate": 2000000
    }
}
```

### Configuration Client (`client_config.py`)

Section RTSP ajoutée:

```python
"rtsp": {
    "enabled": True,
    "host": "localhost",
    "base_port": 8554,
    "resolution": "1280x720",
    "fps": 30,
    "bitrate": 2000000,
    "auto_start_users": True
}
```

## Architecture

### Classes Principales

#### `UserManager` (`user_manager.py`)
- Gestion globale des utilisateurs RTSP
- Création et configuration des utilisateurs
- Coordination des serveurs RTSP

#### `RTSPUser` (dataclass)
- Représentation d'un utilisateur RTSP individuel
- Propriétés: nom, position, rotation, port RTSP, URL

#### `RTSPServer`
- Serveur RTSP individuel pour chaque utilisateur
- Streaming simulé de la vision
- Gestion du cycle de vie (start/stop)

### Intégration Serveur

#### `MinecraftServer` (modifications)
- Initialisation automatique des utilisateurs RTSP au démarrage
- Inclusion dans la liste des joueurs (`player_list`)
- Démarrage/arrêt automatique des serveurs RTSP

#### `PlayerState` (modifications)
- Support des flags `is_rtsp_user` et `is_connected`
- Distinction entre utilisateurs RTSP et clients WebSocket

## Utilisation

### Démarrage du Serveur

```bash
python3 server.py
```

Le serveur affichera:
```
2025-09-24 21:52:01,396 - INFO - Utilisateur créé: Observateur_1 (RTSP: rtsp://localhost:8554/stream)
2025-09-24 21:52:01,396 - INFO - Utilisateur créé: Observateur_2 (RTSP: rtsp://localhost:8555/stream)  
2025-09-24 21:52:01,396 - INFO - Utilisateur créé: Observateur_3 (RTSP: rtsp://localhost:8556/stream)
2025-09-24 21:52:01,396 - INFO - Serveur RTSP actif - Observateur_1: rtsp://localhost:8554/stream
```

### Accès aux Streams RTSP

Les streams RTSP sont disponibles aux URLs:
- `rtsp://localhost:8554/stream` (Observateur_1)
- `rtsp://localhost:8555/stream` (Observateur_2)  
- `rtsp://localhost:8556/stream` (Observateur_3)

### Tests

```bash
# Test complet du système
python3 test_rtsp_users.py

# Test d'intégration serveur
python3 test_integration_final.py
```

## API

### UserManager

```python
from user_manager import user_manager

# Créer les utilisateurs au démarrage
users = user_manager.create_startup_users()

# Obtenir les URLs RTSP
rtsp_urls = user_manager.get_rtsp_urls()

# Démarrer les serveurs RTSP
await user_manager.start_rtsp_servers()
```

### Configuration RTSP

```python
from client_config import config

# Vérifier si RTSP est activé
if config.is_rtsp_enabled():
    rtsp_config = config.get_rtsp_config()
```

## Implémentation Future

Le système actuel utilise des **serveurs RTSP simulés** pour la démonstration. Pour une implémentation complète:

1. **Capture de rendu**: Intégrer avec le moteur de rendu 3D pour capturer la vision de chaque utilisateur
2. **Encodage vidéo**: Utiliser des encodeurs H.264/H.265 pour la compression
3. **Serveur RTSP réel**: Implémenter un serveur RTSP complet (ex: utiliser `opencv-python` avec `gstreamer`)
4. **Streaming réseau**: Support de clients RTSP distants

## Exemples d'Usage

### Client RTSP (VLC, ffmpeg, etc.)

```bash
# Visualiser le stream avec VLC
vlc rtsp://localhost:8554/stream

# Enregistrer avec ffmpeg
ffmpeg -i rtsp://localhost:8554/stream -c copy output.mp4
```

### Intégration Web

```javascript
// Utiliser un player RTSP web
const player = new RTSPPlayer({
    url: 'rtsp://localhost:8554/stream',
    element: document.getElementById('video-container')
});
```

## Logs et Debugging

Le système fournit des logs détaillés:
- Création des utilisateurs RTSP
- État des serveurs RTSP  
- Intégration avec le serveur principal
- Messages de player_list

Utilisez `logging.INFO` pour voir tous les détails d'exécution.

---

**Système implémenté avec succès** ✅
- 3 utilisateurs RTSP configurables
- Serveurs RTSP individuels 
- Intégration complète avec le serveur Minecraft
- Tests complets et validation