# Client Minecraft Abstrait

Cette implémentation fournit une classe `MinecraftClient` abstraite qui permet de contrôler un client Minecraft via l'interface graphique.

## Fonctionnalités

✅ **Interface Graphique Complète**: Basée sur `minecraft_client_fr.py` avec toutes les fonctionnalités de jeu
✅ **Mode Headless**: Fonctionnement sans interface graphique
✅ **Configuration Flexible**: Position, type de bloc configurables

## Installation

```bash
pip install -r requirements.txt
```

Dépendances principales:
- `pyglet==1.5.27` - Interface graphique 3D
- `Pillow>=8.0.0` - Traitement d'images

## Usage Rapide

### 1. Mode GUI

```python
from minecraft_client import MinecraftClient

# Créer un client avec interface graphique
client = MinecraftClient(
    position=(50, 80, 50),
    block_type="STONE"
)

# Lancer le client
client.run()
```

### 2. Mode Headless

```python
from minecraft_client import MinecraftClient

# Créer un client sans interface graphique
client = MinecraftClient(
    position=(100, 60, 100),
    enable_gui=False
)

# Lancer le client headless
client.run()
```

### 3. Scripts de Démonstration

```bash
# Mode GUI
python3 demo_minecraft_client.py --gui

# Mode headless
python3 demo_minecraft_client.py --headless

# Configuration personnalisée
python3 demo_minecraft_client.py --position 100 150 100 --block-type BRICK
```

## Configuration

### Paramètres du Constructeur

```python
MinecraftClient(
    position=(x, y, z),           # Position de départ (défaut: [30, 50, 80])
    block_type="GRASS",           # Type de bloc par défaut  
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
└── Interface Graphique (Pyglet/OpenGL)
    ├── Rendu 3D du monde
    ├── Gestion des entrées utilisateur
    └── Affichage UI/debug
```

## Gestion des Erreurs

- **Mode Headless**: Se lance automatiquement sans GUI si l'affichage n'est pas disponible

## Intégration avec le Code Existant

Cette classe utilise et abstrait `minecraft_client_fr.py` en:

1. **Préservant** toute la logique de jeu existante
2. **Permettant** le mode headless

## Exemples Avancés

Voir `example_usage.py` pour des exemples détaillés incluant:
- Usage basique avec GUI
- Mode headless
- Position personnalisée

## Dépannage

### Problème d'Affichage
```
Warning: Display not available, GUI disabled
```
→ Le client passe automatiquement en mode headless

### Import Pyglet Échoue
```
ImportError: Library "GLU" not found
```
→ Installez: `sudo apt-get install libglu1-mesa-dev`

## Système Simplifié

Cette implémentation fournit une approche simple et directe pour utiliser le client Minecraft.

Les avantages:
- ✅ Simple à utiliser
- ✅ Moins de dépendances
- ✅ Support natif headless/GUI