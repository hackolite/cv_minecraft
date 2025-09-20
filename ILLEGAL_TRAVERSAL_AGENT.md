# Agent de Détection de Traversée Illégale de Blocs

Ce module implémente un agent serveur qui surveille chaque mouvement du joueur et détecte si la nouvelle position du joueur se trouve à l'intérieur d'un bloc solide (traversée non souhaitée).

## Fonctionnalités

### 🚨 Détection Automatique
- Surveillance de tous les mouvements de joueurs
- Détection des positions à l'intérieur de blocs solides
- Distinction entre blocs solides et blocs d'air

### 📝 Logging Détaillé
Format de log conforme aux exigences :

```
2025-09-21 01:12:05,123 - WARNING - 🚨 ILLEGAL BLOCK TRAVERSAL - Player Joueur (UUID) traversed solid block (x, y, z)
2025-09-21 01:12:05,124 - INFO -    Old position: (...)
2025-09-21 01:12:05,124 - INFO -    New position: (...)
2025-09-21 01:12:05,125 - INFO -    Block type: ...
2025-09-21 01:12:05,130 - INFO - Player Joueur (UUID) disconnected for illegal block traversal.
```

### 🔌 Déconnexion Automatique
- Déconnexion immédiate du client en cas de traversée détectée
- Log spécifique du motif de déconnexion

## Architecture

### `IllegalBlockTraversalAgent`
Agent principal encapsulant la logique de détection :

- **`check_traversal()`** : Vérifie si un mouvement constitue une traversée illégale
- **`log_disconnection()`** : Enregistre la déconnexion pour traversée illégale  
- **`_log_illegal_traversal()`** : Génère les logs détaillés selon le format requis

### Intégration Serveur
L'agent est intégré dans `MinecraftServer._handle_player_move()` :

1. Validation des collisions normales (existant)
2. **NOUVEAU** : Vérification de traversée illégale via l'agent
3. Déconnexion automatique si traversée détectée
4. Sinon, traitement normal du mouvement

## Utilisation

### Installation
L'agent est automatiquement initialisé avec le serveur :

```python
# Dans MinecraftServer.__init__()
self.traversal_agent = IllegalBlockTraversalAgent(self.world.world)
```

### Configuration du Logging
```python
import logging
logging.getLogger('illegal_traversal').setLevel(logging.INFO)
```

### Test et Démonstration
```bash
# Tests unitaires
python test_illegal_traversal_agent.py

# Tests d'intégration  
python test_integration_traversal.py

# Démonstration complète
python demo_illegal_traversal_agent.py
```

## Exemples de Détection

### Traversée Illégale Détectée
```
Mouvement: (9.0, 10.0, 10.0) → (10.5, 10.5, 10.5)
Bloc à (10, 10, 10): stone

Résultat: ✅ DÉTECTÉ + DÉCONNEXION
```

### Mouvement Légal
```  
Mouvement: (9.0, 10.0, 10.0) → (8.0, 10.0, 10.0)
Aucun bloc solide à la destination

Résultat: ✅ AUTORISÉ
```

## Compatibilité

- ✅ Compatible avec le système de collision existant
- ✅ N'interfère pas avec les mouvements légaux
- ✅ Fonctionne avec tous les types de blocs (grass, stone, wood, etc.)
- ✅ Ignore correctement les blocs d'air
- ✅ Intégration transparente dans la logique serveur existante

## Tests

Couverture complète des tests :
- Détection de traversée avec différents types de blocs
- Vérification du format de logging exact
- Test des cas limites (blocs d'air, noms de joueur null)
- Intégration avec la logique serveur
- Vérification de la déconnexion automatique