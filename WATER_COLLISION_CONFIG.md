# Water Collision Configuration

## Vue d'ensemble / Overview

Ce document explique comment configurer le comportement de collision des blocs d'eau dans cv_minecraft.

This document explains how to configure water block collision behavior in cv_minecraft.

## Configuration Simple / Simple Configuration

### Français

**Problème résolu:** "je veux marcher sur l'eau, pas couler"

**Solution:** Une simple configuration permet de contrôler si les joueurs marchent sur l'eau ou peuvent nager à travers.

**Comment configurer:**

1. Ouvrez le fichier `server.py`
2. Trouvez la constante `WATER_COLLISION_ENABLED` (environ ligne 45)
3. Modifiez sa valeur:

```python
# Pour marcher sur l'eau (défaut)
WATER_COLLISION_ENABLED = True

# Pour nager à travers l'eau
WATER_COLLISION_ENABLED = False
```

**Comportements:**

- `WATER_COLLISION_ENABLED = True` (défaut)
  - Les blocs d'eau sont solides
  - Les joueurs marchent sur la surface de l'eau
  - Les joueurs ne peuvent pas couler dans l'eau
  
- `WATER_COLLISION_ENABLED = False`
  - Les blocs d'eau n'ont pas de collision
  - Les joueurs peuvent nager à travers l'eau
  - Les joueurs peuvent descendre sous l'eau

### English

**Problem solved:** "I want to walk on water, not sink"

**Solution:** A simple configuration allows you to control whether players walk on water or can swim through it.

**How to configure:**

1. Open the `server.py` file
2. Find the `WATER_COLLISION_ENABLED` constant (around line 45)
3. Change its value:

```python
# To walk on water (default)
WATER_COLLISION_ENABLED = True

# To swim through water
WATER_COLLISION_ENABLED = False
```

**Behaviors:**

- `WATER_COLLISION_ENABLED = True` (default)
  - Water blocks are solid
  - Players walk on the water surface
  - Players cannot sink into water
  
- `WATER_COLLISION_ENABLED = False`
  - Water blocks have no collision
  - Players can swim through water
  - Players can go underwater

## Exemples / Examples

### Démonstration / Demo

Exécutez le script de démonstration pour voir les deux comportements:

Run the demo script to see both behaviors:

```bash
python demo_water_config.py
```

### Tests

Exécutez les tests pour vérifier la configuration:

Run the tests to verify the configuration:

```bash
python tests/test_water_config.py
```

## Détails Techniques / Technical Details

### Implementation

La fonction `get_block_collision()` dans `server.py` vérifie maintenant la configuration:

The `get_block_collision()` function in `server.py` now checks the configuration:

```python
def get_block_collision(block_type: str) -> bool:
    """Get whether a block type has collision."""
    # Air never has collision
    if block_type == BlockType.AIR:
        return False
    
    # Water collision is configurable
    if block_type == BlockType.WATER:
        return WATER_COLLISION_ENABLED
    
    # All other blocks have collision
    return True
```

### Blocs Affectés / Affected Blocks

- **Air** : Toujours sans collision / Always no collision
- **Eau** : Configurable via `WATER_COLLISION_ENABLED` / Configurable via `WATER_COLLISION_ENABLED`
- **Autres blocs** : Toujours avec collision / Always have collision
  - Grass, Stone, Sand, Brick, Wood, Leaf, Camera, User, Cat

### Compatibilité / Compatibility

- La valeur par défaut est `True` (marcher sur l'eau) / Default is `True` (walk on water)
- Tous les tests existants continuent de passer / All existing tests continue to pass
- Aucune modification nécessaire pour le comportement par défaut / No changes needed for default behavior

## Utilisation Avancée / Advanced Usage

### Configuration Dynamique / Dynamic Configuration

Si vous souhaitez changer la configuration pendant l'exécution du serveur:

If you want to change the configuration while the server is running:

```python
import server

# Activer la collision de l'eau
server.WATER_COLLISION_ENABLED = True

# Désactiver la collision de l'eau
server.WATER_COLLISION_ENABLED = False
```

**Note:** Les blocs d'eau existants devront être recréés pour refléter la nouvelle configuration.

**Note:** Existing water blocks will need to be recreated to reflect the new configuration.

## Résumé / Summary

Cette fonctionnalité fournit une configuration simple et claire pour contrôler le comportement de l'eau:

This feature provides a simple and clear configuration to control water behavior:

✅ **Simple:** Une seule variable booléenne / One boolean variable  
✅ **Clair:** Nom explicite et commentaires / Explicit name and comments  
✅ **Flexible:** Changement facile entre les deux modes / Easy to switch between modes  
✅ **Compatible:** Comportement par défaut préservé / Default behavior preserved  

## Questions Fréquentes / FAQ

**Q: Pourquoi la valeur par défaut est-elle `True`?**  
**Q: Why is the default value `True`?**

R: Pour maintenir la compatibilité avec le comportement actuel où les joueurs marchent sur l'eau.

A: To maintain compatibility with the current behavior where players walk on water.

---

**Q: Est-ce que je peux avoir différents comportements pour différentes zones?**  
**Q: Can I have different behaviors for different areas?**

R: Actuellement non, c'est une configuration globale. Une fonctionnalité future pourrait ajouter cela.

A: Currently no, it's a global configuration. A future feature could add this.

---

**Q: Comment puis-je tester les deux modes?**  
**Q: How can I test both modes?**

R: Exécutez `python demo_water_config.py` ou `python tests/test_water_config.py`.

A: Run `python demo_water_config.py` or `python tests/test_water_config.py`.
