# Debug des Positions de Joueurs - cv_minecraft

## Vue d'ensemble

Ce système fournit un debug complet et un système de broadcast pour les positions des joueurs dans le serveur Minecraft. Il permet de tracer en détail tous les mouvements des joueurs et de s'assurer que les mises à jour de position sont correctement diffusées à tous les clients.

## Fonctionnalités implémentées

### 1. Debug détaillé des mouvements (Serveur)

Le serveur affiche maintenant des logs détaillés pour chaque mouvement de joueur :

```
🚶 PLAYER_MOVE DEBUG - Player ValidMover
   Old position: (69, 100, 64)
   New position: (74, 100, 69)  
   Delta: dx=5.00, dy=0.00, dz=5.00
   Distance: 7.07
   Rotation: [90, 0]
```

### 2. Debug du broadcasting

```
📡 Broadcasting position update to 2 other players
📡 Broadcast complete: 2 players notified, 0 disconnected
   ✅ Sent to Alice
   ✅ Sent to Bob_123
```

### 3. Résumé périodique des joueurs

Toutes les 10 secondes, le serveur affiche un résumé de tous les joueurs connectés :

```
📊 PLAYER DEBUG SUMMARY: 3 players connected
   🎯 Alice: pos=(64.0, 20.0, 64.0), vel=[0.0, 0.0, 0.0], on_ground=True, last_move=2.3s ago
   🎯 Bob: pos=(80.0, 25.0, 70.0), vel=[0.0, 0.0, 0.0], on_ground=True, last_move=5.1s ago
   🎯 Charlie: pos=(55.0, 18.0, 90.0), vel=[0.0, 0.0, 0.0], on_ground=True, last_move=1.2s ago
```

### 4. Debug côté client

Les clients affichent maintenant des informations quand ils reçoivent des mises à jour de position :

```
🎮 CLIENT: Updating player Alice
   Old position: (64.0, 20.0, 64.0)
   New position: (69.0, 20.0, 64.0)
   Movement distance: 5.00
   ✅ Player stored successfully at (69.0, 20.0, 64.0)
```

### 5. Anti-cheat avec debug

Le système détecte et log les mouvements suspects :

```
❌ ANTI-CHEAT: Movement distance too large for PlayerX
   Delta: dx=100.00, dy=0.00, dz=50.00
   Distance: 111.80 (Max autorisé: 50.00)
```

## Utilisation

### Démarrer le serveur avec debug

```bash
python server.py
```

Le serveur affichera automatiquement tous les logs de debug des mouvements.

### Tests disponibles

Plusieurs tests sont fournis pour démontrer le système :

```bash
# Test simple de mouvements valides
python test_valid_movements.py

# Test pour déclencher le debug
python test_simple_movement.py

# Test complet avec plusieurs joueurs
python test_player_position_debug.py
```

## Configuration

### Ajuster la fréquence du résumé debug

Dans `server.py`, modifiez la variable `debug_summary_interval` :

```python
debug_summary_interval = 10.0  # Secondes entre les résumés
```

### Ajuster les limites anti-cheat

Dans `server.py`, dans `_handle_player_move` :

```python
# Limite actuelle : 50 unités
if abs(dx) > 50 or abs(dy) > 50 or abs(dz) > 50:
    raise InvalidPlayerDataError("Movement distance too large")
```

### Niveau de logging

Pour plus ou moins de détail, modifiez le niveau de logging :

```python
logging.basicConfig(
    level=logging.DEBUG,  # ou logging.INFO pour moins de détail
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Architecture

### Serveur (server.py)

- `_handle_player_move()` : Debug détaillé des mouvements
- `broadcast_message()` : Debug du broadcasting amélioré  
- `_log_player_debug_summary()` : Résumé périodique des joueurs
- `_physics_update_loop()` : Intégration du résumé debug

### Clients (client.py & minecraft_client_fr.py)

- Debug dans `_handle_server_message()` pour `PLAYER_UPDATE`
- Vérification du stockage des positions reçues
- Logs de confirmation de réception

## Exemple de session debug

```
[2025-09-17 15:27:08] INFO - 🚶 PLAYER_MOVE DEBUG - Player Alice
[2025-09-17 15:27:08] INFO -    Old position: (64, 100, 64)
[2025-09-17 15:27:08] INFO -    New position: (69, 100, 64)
[2025-09-17 15:27:08] INFO -    Delta: dx=5.00, dy=0.00, dz=0.00
[2025-09-17 15:27:08] INFO -    Distance: 5.00
[2025-09-17 15:27:08] INFO -    Rotation: [45, 0]
[2025-09-17 15:27:08] INFO - 📡 Broadcasting position update to 2 other players
[2025-09-17 15:27:08] DEBUG -    ✅ Sent to Bob
[2025-09-17 15:27:08] DEBUG -    ✅ Sent to Charlie  
[2025-09-17 15:27:08] INFO - 📡 Broadcast complete: 2 players notified, 0 disconnected
```

Ce système permet un debug complet et en temps réel de tous les mouvements de joueurs dans le jeu, facilitant grandement le développement et le débogage des fonctionnalités multijoueurs.