# Minecraft Client-Server avec Support Français 🇫🇷

Ce repository propose un client Minecraft amélioré avec support français complet, basé sur le projet de conversion client-serveur de Fogleman's Minecraft.

## 🆕 Nouveau Client Français

### 🎮 `minecraft_client_fr.py` - Client Amélioré

Le nouveau client apporte de nombreuses améliorations spécialement conçues pour les utilisateurs français :

#### ✨ Fonctionnalités Principales
- **🇫🇷 Interface 100% française** - Tous les textes et messages en français
- **⌨️ Support AZERTY natif** - Layout clavier français par défaut (configurable QWERTY)
- **⚙️ Configuration JSON flexible** - Personnalisation complète via fichier `client_config.json`
- **🔄 Reconnexion automatique** - Gestion intelligente des déconnexions
- **🎯 Interface utilisateur avancée** - Feedback visuel, messages informatifs, debug F3
- **🌐 Réseau optimisé** - Client WebSocket robuste avec gestion ping/latence
- **📋 Arguments CLI complets** - Lancement personnalisé en ligne de commande
- **🛠️ Système de launcher** - Aide intégrée et diagnostics automatiques

### 🚀 Démarrage Rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Démarrer le serveur (terminal 1)
python3 server.py

# 3. Lancer le client amélioré (terminal 2)
python3 minecraft_client_fr.py
```

### 📚 Exemples d'Utilisation

```bash
# Connexion locale par défaut
python3 minecraft_client_fr.py

# Serveur distant
python3 minecraft_client_fr.py --server 192.168.1.100:8765

# Mode plein écran avec debug
python3 minecraft_client_fr.py --fullscreen --debug

# Configuration personnalisée
python3 minecraft_client_fr.py --config config_exemple_qwerty.json

# Interface en anglais
python3 minecraft_client_fr.py --lang en

# Aide et diagnostics
python3 launcher.py --help
python3 launcher.py --check
```

### 🎮 Contrôles (Layout AZERTY)

| Touches | Action |
|---------|--------|
| **Z/Q/S/D** | Mouvement (avant/gauche/arrière/droite) |
| **Espace** | Saut |
| **Maj** | S'accroupir |
| **R** | Courir |
| **Tab** | Vol on/off |
| **F3** | Debug on/off |
| **F11** | Plein écran |
| **Échap** | Libérer souris |
| **1-5** | Sélection bloc |
| **Clic gauche** | Détruire bloc |
| **Clic droit** | Placer bloc |

### 📁 Nouveaux Fichiers

| Fichier | Description |
|---------|-------------|
| `minecraft_client_fr.py` | Client principal amélioré (43KB) |
| `client_config.py` | Système de configuration flexible (8KB) |
| `launcher.py` | Lanceur avec aide et diagnostics (5KB) |
| `demo_client_fr.py` | Démonstration interactive (9KB) |
| `test_client_francais.py` | Tests de compatibilité (9KB) |
| `CLIENT_FRANCAIS.md` | Documentation détaillée |
| `client_config.json` | Configuration générée automatiquement |
| `config_exemple_*.json` | Exemples de configuration |

## 🔧 Configuration

Le client génère automatiquement un fichier `client_config.json` personnalisable :

```json
{
    "server": {
        "host": "localhost",
        "port": 8765,
        "auto_reconnect": true
    },
    "graphics": {
        "window_width": 1280,
        "window_height": 720,
        "fov": 70.0
    },
    "controls": {
        "keyboard_layout": "azerty",
        "mouse_sensitivity": 0.15
    },
    "interface": {
        "language": "fr",
        "show_debug_info": true
    },
    "player": {
        "name": "Joueur",
        "movement_speed": 5.0
    }
}
```

## 🧪 Tests et Validation

```bash
# Tests du client français
python3 test_client_francais.py

# Tests du serveur existant
python3 test_minecraft_server.py

# Vérification environnement
python3 launcher.py --check
```

## 🎯 Démonstration

Lancez la démonstration interactive pour découvrir toutes les fonctionnalités :

```bash
python3 demo_client_fr.py
```

---

## 📖 Architecture Client-Serveur (Original)

Ce projet a été converti d'une **architecture monolithique** vers une **architecture client-serveur** pour le support multijoueur.

### 🏗️ Composants

- **🖥️ Serveur (`server.py`)** : Gère le monde autoritaire, connexions WebSocket, logique de jeu
- **🎮 Client (`client.py`)** : Rendu, saisie utilisateur, connexion serveur (version originale)
- **🇫🇷 Client FR (`minecraft_client_fr.py`)** : Version améliorée avec support français
- **📡 Protocole (`protocol.py`)** : Messages et structures de données client-serveur

### ✅ Fonctionnalités Validées

- ✅ **Support multijoueur** : Plusieurs joueurs simultanés
- ✅ **Communication WebSocket** : Synchronisation temps réel
- ✅ **Chargement par chunks** : Transmission optimisée 16x16
- ✅ **Serveur autoritaire** : Prévention triche
- ✅ **Mises à jour temps réel** : Blocs synchronisés entre clients
- ✅ **Suivi mouvement joueurs** : Voir les autres se déplacer

### 🎮 Contrôles Originaux (QWERTY)

- **WASD** : Mouvement 
- **Souris** : Regarder
- **Espace** : Saut
- **Clic gauche** : Détruire bloc
- **Clic droit** : Placer bloc
- **1-5** : Changer type de bloc
- **Tab** : Mode vol
- **R** : Sprint
- **Shift** : S'accroupir
- **Échap** : Libérer curseur

### 📋 Démarrage Original

```shell
# Serveur
python3 server.py

# Client original
python3 client.py

# Version monolithique
python3 main.py
```

## 🔗 Ressources

- **Documentation technique** : `CONVERSION_GUIDE.md`
- **Améliorations serveur** : `SERVER_IMPROVEMENTS.md`
- **Client français** : `CLIENT_FRANCAIS.md`
- **Compatibilité Pyglet** : `PYGLET_COMPATIBILITY.md`

## 🤝 Contribution

- Compatible avec serveur existant (aucune modification requise)
- Protocole inchangé pour compatibilité complète
- Tests automatisés pour validation continue
- Support Windows/Mac/Linux

## 📝 Licence

Même licence que le projet original - voir `LICENSE`

---

**🎮 Original** : [Fogleman's Minecraft](https://github.com/fogleman/Minecraft)  
**🇫🇷 Améliorations françaises** : Assistant IA pour hackolite/cv_minecraft