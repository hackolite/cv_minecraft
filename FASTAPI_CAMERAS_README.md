# FastAPI Camera System

Ce document décrit le nouveau système de caméras FastAPI qui remplace le système RTSP pour visualiser les caméras d'observateurs.

## Vue d'ensemble

Le système RTSP a été remplacé par un serveur FastAPI moderne qui offre:
- Interface web intégrée pour visualiser toutes les caméras
- API REST pour accéder aux images et streams
- WebSocket pour streaming temps réel
- Interface utilisateur responsive

## Démarrage rapide

### 1. Démonstration simple
```bash
python demo_fastapi_cameras.py
```

### 2. Serveur FastAPI seul
```bash
python fastapi_camera_server.py
```

### 3. Serveur intégré (Minecraft + Caméras)
```bash
python server_with_cameras.py
```

## Interface Web

Accédez à `http://localhost:8080` pour l'interface web principale qui affiche:
- Vue grille de toutes les caméras
- Informations de position et rotation pour chaque caméra
- Streams vidéo en temps réel
- Contrôles pour actualiser et voir en détail

## API REST

### Endpoints disponibles

- `GET /` - Interface web principale
- `GET /cameras` - Liste de toutes les caméras (JSON)
- `GET /camera/{id}/image` - Image statique d'une caméra (JPEG)
- `GET /camera/{id}/stream` - Stream MJPEG d'une caméra
- `POST /camera/{id}/move` - Déplacer une caméra
- `WebSocket /ws/camera/{id}` - Stream WebSocket temps réel

### Exemples d'utilisation

```bash
# Lister les caméras
curl http://localhost:8080/cameras

# Obtenir une image
curl http://localhost:8080/camera/{id}/image > image.jpg

# Stream MJPEG (ouvrir dans un navigateur)
http://localhost:8080/camera/{id}/stream
```

## Configuration

La configuration des caméras se fait via `users_config.json`:

```json
{
  "users": [
    {
      "name": "Observateur_1",
      "position": [30, 50, 80],
      "rotation": [0, 0]
    }
  ],
  "camera_settings": {
    "host": "localhost",
    "port": 8080,
    "resolution": "640x480",
    "fps": 30
  }
}
```

## Architecture

### Fichiers clés

- `fastapi_camera_server.py` - Serveur FastAPI principal
- `user_manager.py` - Gestionnaire d'utilisateurs (mis à jour pour FastAPI)
- `observer_camera.py` - Système de caméras (inchangé)
- `server_with_cameras.py` - Serveur combiné Minecraft + Caméras
- `demo_fastapi_cameras.py` - Script de démonstration

### Flux de données

1. `UserManager` crée les utilisateurs et caméras
2. `ObserverCamera` capture les frames depuis les positions d'observateurs
3. `FastAPICameraServer` expose les frames via HTTP/WebSocket
4. Interface web affiche les streams en temps réel

## Migration depuis RTSP

### Changements principaux

| RTSP (ancien) | FastAPI (nouveau) |
|---------------|-------------------|
| `rtsp://localhost:8554/stream` | `http://localhost:8080/camera/{id}/stream` |
| Client RTSP requis | Interface web intégrée |
| Configuration complexe | Configuration simple |
| Protocole binaire | API REST JSON |

### Code de migration

```python
# Ancien (RTSP)
await user_manager.start_rtsp_servers()
urls = user_manager.get_rtsp_urls()

# Nouveau (FastAPI)
await user_manager.start_camera_server()
urls = user_manager.get_camera_urls()
web_url = user_manager.get_web_interface_url()
```

## Avantages du nouveau système

1. **Interface utilisateur** - Interface web moderne et responsive
2. **API standard** - REST API avec JSON, plus facile à intégrer
3. **Performance** - Streaming HTTP plus efficace que RTSP
4. **Simplicité** - Pas besoin de client RTSP externe
5. **Debugging** - Logs et erreurs plus clairs
6. **Extensibilité** - Facile d'ajouter de nouvelles fonctionnalités

## Dépannage

### Problèmes courants

1. **Port 8080 occupé**
   ```bash
   # Vérifier les ports
   netstat -tlnp | grep :8080
   # Changer le port dans camera_settings
   ```

2. **Caméras inactives**
   ```bash
   # Vérifier les logs
   python demo_fastapi_cameras.py
   ```

3. **Images noires**
   - Normal en mode headless (sans OpenGL)
   - Les caméras génèrent des images de test colorées

### Logs utiles

```bash
# Démarrage avec logs détaillés
python -m uvicorn fastapi_camera_server:fastapi_camera_server.app --host 0.0.0.0 --port 8080 --log-level debug
```

## Développement

### Ajouter une nouvelle fonctionnalité

1. Modifier `fastapi_camera_server.py` pour ajouter l'endpoint
2. Mettre à jour l'interface web si nécessaire
3. Tester avec `demo_fastapi_cameras.py`

### Tests

```bash
# Test des caméras
python test_camera_streaming.py

# Test de l'API
curl http://localhost:8080/cameras | jq .
```