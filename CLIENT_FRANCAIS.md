# Client Minecraft Français Amélioré

Ce repository propose un **client Minecraft amélioré** utilisant Pyglet avec un support complet pour les utilisateurs français.

## 🆕 Nouvelles Fonctionnalités

### ✨ Client Amélioré (`minecraft_client_fr.py`)

Le nouveau client apporte de nombreuses améliorations par rapport au client original :

#### 🇫🇷 Support Français Natif
- **Interface en français** avec textes localisés
- **Support AZERTY** par défaut (configurable QWERTY)
- **Documentation et messages d'erreur en français**
- **Configuration intuitive** avec valeurs par défaut françaises

#### 🎮 Expérience Utilisateur Améliorée
- **Reconnexion automatique** en cas de perte de connexion
- **Messages informatifs** avec feedback visuel
- **Gestion d'erreurs robuste** avec messages explicites
- **Interface de debug avancée** (F3 pour basculer)
- **Indicateurs de performance** (FPS, ping, statut connexion)
- **Vue du dessus** (F6) pour une perspective aérienne sur votre personnage
- **📹 Enregistrement de gameplay** (F9) pour capturer vos sessions de jeu

#### ⚙️ Configuration Flexible
- **Fichier de configuration JSON** (`client_config.json`)
- **Arguments en ligne de commande** pour personnalisation rapide
- **Sauvegarde automatique** des préférences
- **Layout clavier configurable** (AZERTY/QWERTY)
- **Paramètres graphiques ajustables**

#### 🌐 Réseau Optimisé
- **Client WebSocket avancé** avec gestion d'erreurs
- **Ping et statistiques de connexion**
- **Gestion de la latence** et reconnexion intelligente
- **Compatible avec le serveur existant**

## 🚀 Installation et Utilisation

### Prérequis
```bash
pip install -r requirements.txt
```

### Démarrage Rapide

1. **Démarrer le serveur** (terminal 1):
```bash
python3 server.py
```

2. **Lancer le client amélioré** (terminal 2):
```bash
python3 minecraft_client_fr.py
```

Ou utilisez le lanceur pour plus d'options :
```bash
python3 launcher.py --help
```

### Options de Lancement

```bash
# Connexion locale par défaut
python3 minecraft_client_fr.py

# Serveur distant
python3 minecraft_client_fr.py --server 192.168.1.100:8765

# Mode plein écran avec debug
python3 minecraft_client_fr.py --fullscreen --debug

# Configuration personnalisée
python3 minecraft_client_fr.py --config mon_config.json

# Interface en anglais
python3 minecraft_client_fr.py --lang en
```

## 🎮 Contrôles

### Layout AZERTY (défaut)
- **Z/Q/S/D** : Mouvement (avant/gauche/arrière/droite)
- **Espace** : Saut
- **Maj Gauche** : S'accroupir
- **R** : Courir
- **Tab** : Activer/désactiver le vol
- **F3** : Informations de debug
- **F5** : Afficher/masquer le cube joueur
- **F6** : Basculer en vue du dessus (top-down)
- **F9** : 📹 Démarrer/Arrêter l'enregistrement de gameplay
- **F11** : Plein écran
- **Échap** : Libérer la souris
- **1-5** : Sélection de bloc

### Souris
- **Clic gauche** : Détruire un bloc
- **Clic droit** : Placer un bloc
- **Mouvement** : Regarder autour

### 📹 Enregistrement de Gameplay

Le client intègre un système d'enregistrement qui capture vos sessions de jeu :

- **F9** : Démarrer/Arrêter l'enregistrement
- Les frames sont sauvegardées dans le dossier `recordings/`
- Chaque session crée un sous-dossier avec timestamp
- Format de sortie : PNG (convertible en vidéo avec ffmpeg)
- Indicateur visuel dans l'interface de debug

**Exemple d'utilisation :**
1. Appuyez sur **F9** pour démarrer l'enregistrement
2. Jouez normalement (l'indicateur 🔴 REC apparaît avec F3)
3. Appuyez à nouveau sur **F9** pour arrêter
4. Trouvez vos frames dans `recordings/session_YYYYMMDD_HHMMSS/`

Pour plus de détails, consultez [GAMEPLAY_RECORDING.md](GAMEPLAY_RECORDING.md)

## ⚙️ Configuration

Le client génère automatiquement un fichier `client_config.json` avec toutes les options :

```json
{
    "server": {
        "host": "localhost",
        "port": 8765,
        "auto_reconnect": true,
        "connection_timeout": 10
    },
    "graphics": {
        "window_width": 1280,
        "window_height": 720,
        "fullscreen": false,
        "fov": 70.0,
        "render_distance": 60.0
    },
    "controls": {
        "keyboard_layout": "azerty",
        "mouse_sensitivity": 0.15,
        "invert_mouse_y": false
    },
    "interface": {
        "language": "fr",
        "show_debug_info": true,
        "crosshair_color": [255, 255, 255]
    },
    "player": {
        "name": "Joueur",
        "movement_speed": 5.0,
        "jump_speed": 8.0
    }
}
```

## 🔧 Fonctionnalités Techniques

### Architecture Réseau
- **Client WebSocket asynchrone** avec thread dédié
- **Gestion des messages protocole** robuste
- **Reconnexion automatique** avec backoff exponentiel
- **Statistiques de connexion** en temps réel

### Rendu Graphique
- **Pyglet 1.5.27** pour compatibilité maximum
- **Batch rendering** optimisé pour les performances
- **Gestion des secteurs** pour le culling
- **Support multi-résolution** et plein écran

### Gestion d'Erreurs
- **Try-catch complets** sur toutes les opérations critiques
- **Messages d'erreur localisés** et informatifs
- **Logging structuré** pour le debugging
- **Récupération gracieuse** des erreurs réseau

## 📋 Comparaison avec le Client Original

| Fonctionnalité | Client Original | Client Amélioré |
|---|---|---|
| Langue | Anglais | **Français + Anglais** |
| Clavier | QWERTY fixe | **AZERTY/QWERTY configurable** |
| Configuration | Code dur | **Fichier JSON flexible** |
| Reconnexion | Manuelle | **Automatique** |
| Interface | Basique | **Avancée avec feedback** |
| Gestion d'erreurs | Minimale | **Robuste et informative** |
| Performance | Statiques | **Métriques en temps réel** |
| Arguments CLI | Aucun | **Complets avec aide** |

## 🐛 Dépannage

### Problèmes Courants

1. **"Library GLU not found"**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libglu1-mesa-dev
   
   # CentOS/RHEL
   sudo yum install mesa-libGLU-devel
   ```

2. **"Connection failed"**
   - Vérifier que le serveur fonctionne
   - Tester avec `python3 test_minecraft_server.py`
   - Vérifier l'adresse/port dans la configuration

3. **Latence élevée**
   - Utiliser F3 pour voir le ping
   - Ajuster `connection_timeout` dans la config
   - Vérifier la qualité réseau

### Outils de Diagnostic

```bash
# Vérifier l'environnement
python3 launcher.py --check

# Test de connexion serveur
python3 test_minecraft_server.py

# Mode debug complet
python3 minecraft_client_fr.py --debug
```

## 🤝 Contribution

Le client amélioré maintient la compatibilité complète avec :
- Le protocole existant (`protocol.py`)
- Le serveur existant (`server.py`) 
- Les tests existants (`test_minecraft_server.py`)

Aucune modification côté serveur n'est nécessaire !

## 📝 Licence

Même licence que le projet original (voir `LICENSE`).

---

**Auteur**: Assistant IA pour hackolite/cv_minecraft  
**Base**: Client Minecraft de Fogleman  
**Améliorations**: Support français, configuration flexible, interface avancée