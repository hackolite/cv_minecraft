# Guide de Dépannage - FastAPI Camera Server

## Problème: "curl: (7) Failed to connect to localhost port 8080 after 0 ms: Connection refused"

Cette erreur indique que le serveur FastAPI n'est pas en cours d'exécution ou n'est pas accessible.

### Solutions Rapides

#### 1. Diagnostic Automatique
```bash
python server_health_check.py
```

Ce script vous donnera un diagnostic complet et des solutions personnalisées.

#### 2. Démarrer le Serveur
```bash
# Option 1: Démonstration simple
python demo_fastapi_cameras.py

# Option 2: Serveur complet avec Minecraft
python server_with_cameras.py
```

#### 3. Vérification Manuelle
```bash
# Vérifier si le port est occupé
netstat -tlnp | grep :8080

# Tester la connexion
curl http://localhost:8080/health
```

### Causes Communes et Solutions

#### Port 8080 déjà utilisé
**Symptômes:** Le serveur ne démarre pas ou utilise un port différent
**Solutions:**
- Arrêtez l'autre processus utilisant le port
- Le serveur trouvera automatiquement un port libre (8081, 8082, etc.)
- Modifiez le port dans `users_config.json`

#### Serveur pas démarré
**Symptômes:** Connection refused, port libre
**Solutions:**
1. Démarrez le serveur avec `python demo_fastapi_cameras.py`
2. Vérifiez les dépendances: `pip install -r requirements.txt`
3. Consultez les logs pour des erreurs de démarrage

#### Timeout de démarrage
**Symptômes:** Le serveur met du temps à répondre
**Solutions:**
- Attendez quelques secondes après le démarrage
- Vérifiez les ressources système (CPU, mémoire)
- Utilisez le diagnostic: `python server_health_check.py`

#### Erreurs de caméras
**Symptômes:** Serveur démarre mais caméras inactives
**Solutions:**
- Normal en mode headless (sans OpenGL)
- Les caméras génèrent des images de test colorées
- Vérifiez les logs du serveur

### Tests de Connectivité

#### Test Complet
```bash
python tests/test_server_connectivity.py
```

#### Tests Manuels
```bash
# Test de base
curl -I http://localhost:8080/

# Test de santé
curl http://localhost:8080/health

# Test des caméras
curl http://localhost:8080/cameras

# Interface web
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
```

### Configuration

#### Fichier `users_config.json`
```json
{
  "users": [...],
  "camera_settings": {
    "host": "localhost",
    "port": 8080,
    "resolution": "640x480",
    "fps": 30
  }
}
```

#### Variables d'environnement
- Aucune configuration supplémentaire requise
- Le serveur détecte automatiquement le mode headless

### Logs Utiles

#### Démarrage avec logs détaillés
```bash
python -m uvicorn fastapi_camera_server:fastapi_camera_server.app --host 0.0.0.0 --port 8080 --log-level debug
```

#### Logs de diagnostic
- `[INFO] Starting FastAPI Camera Server on http://localhost:8080` ✅ Normal
- `[ERROR] Port 8080 is already in use` ⚠️ Port occupé
- `[ERROR] Failed to start FastAPI server` ❌ Erreur critique

### Support

1. **Diagnostic automatique:** `python server_health_check.py`
2. **Test de connectivité:** `python tests/test_server_connectivity.py`
3. **Démonstration:** `python demo_fastapi_cameras.py`
4. **Serveur complet:** `python server_with_cameras.py`

### Architecture

Le système comprend:
- **FastAPI Server** (port 8080) - Interface web et API REST
- **Caméras d'observateurs** - Capture d'images depuis les positions d'observateurs
- **Interface web** - Visualisation en temps réel des streams
- **API REST** - Accès programmatique aux caméras

Pour plus d'informations, consultez `FASTAPI_CAMERAS_README.md`.