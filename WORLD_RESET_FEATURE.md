# World Reset Feature / Fonction de Réinitialisation du Monde

## Description

Cette fonctionnalité permet de réinitialiser le monde du serveur au terrain naturel en supprimant tous les blocs ajoutés par les joueurs, les caméras, et les utilisateurs, tout en conservant uniquement le terrain généré naturellement.

This feature allows resetting the server world to natural terrain by removing all player-added blocks, cameras, and users, while keeping only the naturally generated terrain.

## Utilisation / Usage

### Démarrer le serveur avec réinitialisation du monde / Start server with world reset

```bash
python server.py --reset-world
```

### Options de ligne de commande / Command-line options

```bash
python server.py --help
```

Affiche / Shows:
```
usage: server.py [-h] [--host HOST] [--port PORT] [--reset-world]

Serveur Minecraft - Serveur de jeu multijoueur

options:
  -h, --help     show this help message and exit
  --host HOST    Adresse hôte du serveur (défaut: localhost)
  --port PORT    Port du serveur (défaut: 8765)
  --reset-world  Réinitialiser le monde au terrain naturel (supprime tous les
                 blocs avec propriétaire, caméras, utilisateurs et blocs ajoutés)
```

## Blocs conservés / Blocks kept

Le mode réinitialisation conserve uniquement les blocs de terrain naturel suivants :
The reset mode only keeps the following natural terrain blocks:

- 🌱 **GRASS** (Herbe / Grass)
- 🏖️ **SAND** (Sable / Sand)
- 🪨 **STONE** (Pierre / Stone)
- 💧 **WATER** (Eau / Water)
- 🪵 **WOOD** (Bois / Wood - troncs d'arbres / tree trunks)
- 🍃 **LEAF** (Feuilles / Leaves - feuillage des arbres / tree foliage)

## Blocs supprimés / Blocks removed

Les types de blocs suivants sont supprimés lors de la réinitialisation :
The following block types are removed during reset:

- 📷 **CAMERA** - Blocs caméra (avec ou sans propriétaire / with or without owner)
- 👤 **USER** - Blocs utilisateur (représentant les joueurs / representing players)
- 🐱 **CAT** - Blocs chat / Cat blocks
- 🧱 **BRICK** - Briques / Bricks
- Et tout autre bloc ajouté par les joueurs / And any other player-added blocks

### Critères de suppression / Removal criteria

Un bloc est supprimé si / A block is removed if:

1. Il possède un **propriétaire** (`owner` field) - typiquement les caméras placées par les joueurs
   / It has an **owner** (owner field) - typically player-placed cameras
2. Il possède un **block_id** - caméras et blocs utilisateur
   / It has a **block_id** - cameras and user blocks
3. Son **type** n'est pas dans la liste des blocs naturels
   / Its **type** is not in the natural blocks list

## Exemples d'utilisation / Usage examples

### Démarrage normal / Normal startup
```bash
# Conserve tous les blocs (caméras, joueurs, constructions)
# Keeps all blocks (cameras, players, constructions)
python server.py
```

### Démarrage avec réinitialisation / Startup with reset
```bash
# Supprime tous les blocs non-naturels au démarrage
# Removes all non-natural blocks at startup
python server.py --reset-world
```

### Serveur sur un hôte/port spécifique avec réinitialisation
### Server on specific host/port with reset
```bash
python server.py --host 0.0.0.0 --port 9000 --reset-world
```

## Détails techniques / Technical details

### Méthode `reset_to_natural_terrain()`

Cette méthode est définie dans la classe `GameWorld` et effectue les opérations suivantes :
This method is defined in the `GameWorld` class and performs the following operations:

1. **Identification** - Parcourt tous les blocs du monde
   / Iterates through all blocks in the world
2. **Filtrage** - Identifie les blocs à supprimer selon les critères
   / Identifies blocks to remove based on criteria
3. **Nettoyage** - Supprime les blocs et met à jour les structures de données :
   / Removes blocks and updates data structures:
   - `world` dictionary (position → block_data)
   - `sectors` dictionary (sector → positions list)
   - `block_id_map` dictionary (block_id → position)
4. **Logging** - Enregistre le nombre de blocs supprimés
   / Logs the number of blocks removed

### Intégration / Integration

La fonctionnalité est intégrée via :
The feature is integrated through:

- Paramètre `reset_to_natural` dans `GameWorld.__init__()`
  / `reset_to_natural` parameter in `GameWorld.__init__()`
- Paramètre `reset_world` dans `MinecraftServer.__init__()`
  / `reset_world` parameter in `MinecraftServer.__init__()`
- Argument `--reset-world` dans la fonction `main()`
  / `--reset-world` argument in `main()` function

## Tests

Des tests unitaires complets sont disponibles dans :
Comprehensive unit tests are available in:

- `tests/test_world_reset.py` - Tests de la méthode reset_to_natural_terrain()
- `tests/test_server_reset.py` - Tests de l'intégration serveur

Pour exécuter les tests / To run the tests:
```bash
python tests/test_world_reset.py
python tests/test_server_reset.py
```

## Cas d'usage / Use cases

### 1. Nettoyage après tests / Cleanup after testing
Après avoir testé des fonctionnalités avec de nombreuses caméras ou constructions, réinitialisez rapidement le monde.
After testing features with many cameras or constructions, quickly reset the world.

### 2. Sessions de jeu fraîches / Fresh game sessions
Démarrez chaque session de jeu avec un monde vierge sans blocs précédents.
Start each game session with a clean world without previous blocks.

### 3. Maintenance / Maintenance
Retour à un état connu et stable du monde.
Return to a known and stable world state.

## Notes importantes / Important notes

⚠️ **Attention** : Cette opération est irréversible. Tous les blocs non-naturels seront définitivement supprimés.
⚠️ **Warning**: This operation is irreversible. All non-natural blocks will be permanently removed.

💡 **Conseil** : Utilisez cette option uniquement au démarrage du serveur. Une fois le serveur lancé, les joueurs peuvent ajouter de nouveaux blocs normalement.
💡 **Tip**: Use this option only at server startup. Once the server is running, players can add new blocks normally.

## Voir aussi / See also

- `BLOCK_METADATA_SYSTEM.md` - Documentation du système de métadonnées de blocs
- `CAMERA_OWNER_SYSTEM.md` - Documentation du système de propriétaire de caméra
