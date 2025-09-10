# Conversion Ursina → Panda3D - Guide Technique

## Changements Majeurs Effectués

### 1. **Requirements (requirements.txt)**
```diff
- ursina==7.0.0
+ Panda3D
  websockets==12.0
  asyncio
```

### 2. **Client (client.py) - Conversion Complète**

#### **Architecture**
- **Avant**: Classe `MinecraftClient` utilisant Ursina App
- **Après**: Classe `MinecraftClient(ShowBase)` héritant de Panda3D ShowBase

#### **Rendu 3D**
- **Avant**: `Entity(model='cube', color=color.green)`
- **Après**: `CardMaker` avec 6 faces pour créer des cubes

#### **Caméra et Mouvement**
- **Avant**: `FirstPersonController()` d'Ursina
- **Après**: Contrôleur manuel avec `camera.setPos()` et physique personnalisée

#### **Interface Utilisateur**
- **Avant**: `Text()` d'Ursina
- **Après**: `OnscreenText()` et `DirectGUI` de Panda3D

#### **Gestion des Entrées**
- **Avant**: `held_keys`, `mouse.left`, etc.
- **Après**: `accept()` avec callbacks et `key_map`

### 3. **Serveur (server.py)**
- ✅ **Aucun changement** - Le serveur est indépendant du moteur de rendu
- Toute la logique WebSocket et gestion du monde préservée

### 4. **Tests (test_connection.py)**
- Mise à jour des imports pour Panda3D
- Tests simplifiés pour éviter l'initialisation graphique complète

### 5. **Documentation (README.md)**
- Références mises à jour: Ursina → Panda3D
- Dépendances actualisées

## Fonctionnalités Préservées

- ✅ Communication WebSocket client-serveur
- ✅ Génération de monde 3D
- ✅ Mouvement ZQSD + gravité + saut
- ✅ Placement/destruction de blocs
- ✅ Multijoueur
- ✅ Chat
- ✅ Types de blocs (grass, stone, wood, dirt, sand, water)

## Avantages de Panda3D

1. **Moteur plus mature** et stable
2. **Meilleure performance** pour le rendu 3D
3. **Documentation extensive** et communauté active
4. **Meilleur support** des fonctionnalités avancées
5. **Plus de contrôle** sur le pipeline de rendu

## Instructions d'Utilisation

### Installation
```bash
pip install -r requirements.txt
```

### Démarrage
```bash
# Terminal 1: Serveur
python3 server.py

# Terminal 2: Client  
python3 client.py
```

### Contrôles (inchangés)
- **ZQSD**: Déplacement
- **Espace**: Saut
- **Souris**: Regarder autour
- **Clic gauche**: Détruire bloc
- **Clic droit**: Placer bloc
- **1-6**: Changer type de bloc
- **T**: Chat
- **ESC**: Quitter

La conversion est complète et fonctionnelle! 🎉