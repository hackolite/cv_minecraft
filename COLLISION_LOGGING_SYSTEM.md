# Système de Logging des Collisions - cv_minecraft

## Vue d'ensemble

Le système de collision de cv_minecraft a été amélioré avec un logging détaillé qui enregistre toutes les collisions avec des informations complètes incluant les coordonnées AABB, l'heure et les positions comme requis.

## Fonctionnalités

### 🚫 Logging des Collisions avec Blocs

Quand un joueur entre en collision avec un bloc solide, le système log automatiquement:

- **Heure**: Timestamp précis avec millisecondes
- **Position joueur**: Coordonnées (x, y, z) du joueur
- **Position bloc**: Coordonnées (x, y, z) du bloc 
- **Type bloc**: Type de matériau (stone, grass, wood, etc.)
- **AABB Joueur**: Coordonnées min/max de la boîte de collision du joueur
- **AABB Bloc**: Coordonnées min/max de la boîte de collision du bloc

### 👥 Logging des Collisions entre Joueurs  

Quand deux joueurs entrent en collision, le système log:

- **Heure**: Timestamp précis avec millisecondes
- **Position joueur 1**: Coordonnées du premier joueur
- **Position joueur 2**: Coordonnées du second joueur
- **AABB Joueur 1**: Coordonnées min/max du premier joueur
- **AABB Joueur 2**: Coordonnées min/max du second joueur

## Exemple de Logs

### Collision avec un Bloc
```
🚫 COLLISION DÉTECTÉE - Bloc
   Heure: 2025-09-20 22:19:39.896
   Position joueur: (10.500, 10.500, 10.500)
   Position bloc: (10, 10, 10)
   Type bloc: stone
   AABB Joueur: min=(10.000, 10.500, 10.000) max=(11.000, 11.500, 11.000)
   AABB Bloc: min=(10.000, 10.000, 10.000) max=(11.000, 11.000, 11.000)
```

### Collision entre Joueurs
```
🚫 COLLISION DÉTECTÉE - Joueur vs Joueur
   Heure: 2025-09-20 22:19:39.897
   Position joueur 1: (10.300, 10.000, 10.200)
   Position joueur 2: (10.000, 10.000, 10.000)
   AABB Joueur 1: min=(9.800, 10.000, 9.700) max=(10.800, 11.000, 10.700)
   AABB Joueur 2: min=(9.500, 10.000, 9.500) max=(10.500, 11.000, 10.500)
```

## Configuration

### Logger utilisé
```python
collision_logger = logging.getLogger('minecraft_collision')
```

### Activation du logging
Le logging est automatiquement activé quand une collision est détectée. Pour configurer le niveau de logging:

```python
import logging
logging.getLogger('minecraft_collision').setLevel(logging.INFO)
```

## Tests et Démonstration

### Tests automatisés
- `test_collision_logging.py` - Tests complets du système de logging
- Vérifie que tous les champs requis sont présents
- Teste les collisions bloc et joueur
- Valide qu'aucun log n'est généré sans collision

### Démonstration
- `demo_collision_logging.py` - Démonstration interactive
- Montre des exemples de collisions en temps réel
- Affiche les logs formatés avec toutes les informations

## Intégration

### Méthodes modifiées
- `UnifiedCollisionManager.check_block_collision()` - Logging des collisions avec blocs
- `UnifiedCollisionManager.check_player_collision()` - Logging des collisions entre joueurs

### Compatibilité
- 100% compatible avec le code existant
- Aucun impact sur les performances quand pas de collision
- Tous les tests existants passent toujours
- API inchangée pour les utilisateurs

## Performance

- **Impact minimal**: Logging seulement en cas de collision réelle
- **Format efficace**: Informations structurées et lisibles  
- **Thread-safe**: Compatible avec le système multi-joueurs
- **Configurable**: Peut être désactivé via configuration logging standard

## Utilisation

Le système est automatiquement actif dès l'importation de `minecraft_physics.py`. Aucune configuration supplémentaire n'est requise pour obtenir les logs de collision avec toutes les informations demandées (coordonnées AABB, heure, positions).

Pour voir les logs en action, exécutez:
```bash
python demo_collision_logging.py
```

Pour tester le système:
```bash  
python test_collision_logging.py
```