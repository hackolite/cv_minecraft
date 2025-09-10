# cv_minecraft

Un client et serveur Minecraft-like développé en Python avec Ursina pour le rendu 3D et WebSockets pour la communication réseau.

## 🎮 Fonctionnalités

- **Client 3D** : Interface graphique avec Ursina Engine
- **Serveur multijoueur** : Gestion de plusieurs joueurs simultanément
- **Monde persistant** : Génération et sauvegarde du monde
- **Interactions** : Placer et détruire des blocs
- **Chat** : Communication entre joueurs
- **Types de blocs** : Grass, stone, wood, dirt, sand, water

## 📋 Prérequis

- Python 3.8+
- Dépendances listées dans `requirements.txt`

## 🚀 Installation

1. **Cloner le repository** :
```bash
git clone <repository_url>
cd cv_minecraft
```

2. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

## 🎯 Utilisation

### Démarrer le serveur

```bash
python3 server.py
```

Le serveur démarrera sur `localhost:8765` par défaut.

### Démarrer le client

```bash
python3 client.py
```

Le client vous demandera :
- Adresse du serveur (par défaut : localhost)
- Port du serveur (par défaut : 8765)  
- Nom du joueur (par défaut : Joueur)

### Contrôles du jeu

- **ZQSD** : Se déplacer
- **Souris** : Regarder autour
- **Clic gauche** : Détruire un bloc
- **Clic droit** : Placer un bloc
- **1-6** : Changer le type de bloc sélectionné
- **T** : Ouvrir/fermer le chat
- **ESC** : Quitter le jeu

## 🧪 Tests

Pour vérifier que tout fonctionne correctement :

```bash
# Démarrer le serveur dans un terminal
python3 server.py

# Dans un autre terminal, lancer les tests
python3 test_connection.py
```

## 🔧 Résolution des problèmes

### "Le client ne fonctionne pas"

1. **Vérifier les dépendances** :
```bash
pip install -r requirements.txt
```

2. **Vérifier que le serveur est démarré** :
```bash
python3 server.py
```

3. **Tester la connexion** :
```bash
python3 test_connection.py
```

### Erreurs courantes

- **ModuleNotFoundError** : Installez les dépendances avec `pip install -r requirements.txt`
- **ConnectionRefusedError** : Le serveur n'est pas démarré ou n'est pas accessible
- **Erreurs graphiques** : Vérifiez que votre système supporte OpenGL

## 📁 Structure du projet

```
cv_minecraft/
├── client.py              # Client Minecraft avec interface 3D
├── server.py              # Serveur WebSocket multijoueur
├── test_connection.py     # Tests de connectivité
├── requirements.txt       # Dépendances Python
└── README.md             # Cette documentation
```

## 🔗 Dépendances

- **ursina** : Moteur 3D pour le client
- **websockets** : Communication client-serveur
- **asyncio** : Programmation asynchrone
