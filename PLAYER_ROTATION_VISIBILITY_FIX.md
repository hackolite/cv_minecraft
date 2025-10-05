# Player Rotation Visibility Fix

## Problème / Problem

**FR**: "l'utilisateur tourne autour de la brick mais on ne vois pas cet utilisateur originel, soit l'update ne focntionne pas, soit les utilisateurs ne sont pas visible, vérifie ça"

**EN**: "the user rotates around the brick but we don't see this original user, either the update doesn't work or the users are not visible, check that"

## Analyse / Analysis

### Symptôme / Symptom
Quand un joueur tourne (change sa direction de vue), le cube qui le représente (local_player_cube) ne tourne pas. Résultat : quand on regarde depuis une caméra ou quand un autre joueur le voit, la rotation n'est pas visible.

When a player rotates (changes their viewing direction), the cube representing them (local_player_cube) doesn't rotate. Result: when viewing from a camera or when another player sees them, the rotation isn't visible.

### Cause Racine / Root Cause
Le code mettait à jour `local_player_cube.position` mais PAS `local_player_cube.rotation`, même si:
1. La rotation était envoyée au serveur dans les messages `PLAYER_MOVE`
2. Le serveur renvoyait la rotation dans les messages `PLAYER_UPDATE`
3. La classe `Cube` avait une méthode `update_rotation()` disponible

The code was updating `local_player_cube.position` but NOT `local_player_cube.rotation`, even though:
1. Rotation was being sent to the server in `PLAYER_MOVE` messages
2. The server was sending rotation back in `PLAYER_UPDATE` messages
3. The `Cube` class had an `update_rotation()` method available

## Solution Appliquée / Applied Solution

### Fix 1: Mise à jour depuis le serveur / Update from Server
**Fichier / File**: `minecraft_client_fr.py`, lignes 306-318

**Avant / Before**:
```python
elif message.type == MessageType.PLAYER_UPDATE:
    player_data = message.data
    player_id = player_data["id"]
    if player_id == self.player_id:
        self.window.position = tuple(player_data["position"])
        # ❌ Rotation is NOT extracted
        self.window.dy = player_data["velocity"][1]
        self.window.on_ground = player_data.get("on_ground", False)
        if self.window.local_player_cube:
            self.window.local_player_cube.update_position(self.window.position)
            # ❌ Rotation is NOT updated
            self.window.local_player_cube.velocity = player_data["velocity"]
            self.window.local_player_cube.on_ground = player_data.get("on_ground", False)
```

**Après / After**:
```python
elif message.type == MessageType.PLAYER_UPDATE:
    player_data = message.data
    player_id = player_data["id"]
    if player_id == self.player_id:
        self.window.position = tuple(player_data["position"])
        self.window.rotation = tuple(player_data["rotation"])  # ✅ Extract rotation
        self.window.dy = player_data["velocity"][1]
        self.window.on_ground = player_data.get("on_ground", False)
        if self.window.local_player_cube:
            self.window.local_player_cube.update_position(self.window.position)
            self.window.local_player_cube.update_rotation(self.window.rotation)  # ✅ Update rotation
            self.window.local_player_cube.velocity = player_data["velocity"]
            self.window.local_player_cube.on_ground = player_data.get("on_ground", False)
```

### Fix 2: Mise à jour locale / Local Update
**Fichier / File**: `minecraft_client_fr.py`, lignes 1235-1254

**Avant / Before**:
```python
def on_mouse_motion(self, x, y, dx, dy):
    """Gère le mouvement de la souris."""
    if self.exclusive:
        sensitivity = config.get("controls", "mouse_sensitivity", 0.15)
        invert_y = config.get("controls", "invert_mouse_y", False)

        x_rot, y_rot = self.rotation
        x_rot += dx * sensitivity
        
        if not self.top_down_view:
            y_rot += dy * sensitivity * (-1 if invert_y else 1)
            y_rot = max(-90, min(90, y_rot))
        
        self.rotation = (x_rot, y_rot)
        # ❌ local_player_cube rotation NOT updated
```

**Après / After**:
```python
def on_mouse_motion(self, x, y, dx, dy):
    """Gère le mouvement de la souris."""
    if self.exclusive:
        sensitivity = config.get("controls", "mouse_sensitivity", 0.15)
        invert_y = config.get("controls", "invert_mouse_y", False)

        x_rot, y_rot = self.rotation
        x_rot += dx * sensitivity
        
        if not self.top_down_view:
            y_rot += dy * sensitivity * (-1 if invert_y else 1)
            y_rot = max(-90, min(90, y_rot))
        
        self.rotation = (x_rot, y_rot)
        
        # ✅ Update local player cube rotation to match view rotation
        if self.local_player_cube:
            self.local_player_cube.update_rotation(self.rotation)
```

## Impact / Impact

### Avant le Fix / Before Fix
- ❌ Le cube du joueur ne tournait jamais / Player cube never rotated
- ❌ Dans les vues caméra, le joueur apparaissait toujours orienté dans la même direction / In camera views, player always appeared facing the same direction
- ❌ Les autres joueurs ne voyaient pas la rotation / Other players didn't see the rotation
- ❌ Expérience visuelle incomplète / Incomplete visual experience

### Après le Fix / After Fix
- ✅ Le cube du joueur tourne en temps réel / Player cube rotates in real-time
- ✅ Dans les vues caméra, le joueur est visible avec la bonne orientation / In camera views, player is visible with correct orientation
- ✅ Les autres joueurs voient la rotation / Other players see the rotation
- ✅ Expérience visuelle complète et cohérente / Complete and consistent visual experience

## Tests

### Nouveau Test / New Test
**Fichier / File**: `tests/test_player_rotation_update.py`

Ce test vérifie / This test verifies:
1. ✅ `on_mouse_motion` met à jour `local_player_cube.rotation` / updates `local_player_cube.rotation`
2. ✅ Le gestionnaire `PLAYER_UPDATE` met à jour `local_player_cube.rotation` / `PLAYER_UPDATE` handler updates `local_player_cube.rotation`
3. ✅ La rotation est envoyée au serveur dans les messages `PLAYER_MOVE` / Rotation is sent to server in `PLAYER_MOVE` messages

### Tests Existants / Existing Tests
- ✅ `test_camera_player_visibility.py` - Toujours OK / Still passing
- ✅ `test_cube_system.py` - Toujours OK / Still passing

## Technique: Flux de Rotation / Rotation Flow

```
1. Joueur bouge la souris / Player moves mouse
   │
   ├─> on_mouse_motion()
   │   │
   │   ├─> self.rotation = (x_rot, y_rot)  ← Mise à jour de la vue / View update
   │   │
   │   └─> self.local_player_cube.update_rotation(self.rotation)  ← ✅ NOUVEAU / NEW
   │
   ├─> _send_position_update()
   │   │
   │   └─> create_player_move_message(self.position, self.rotation)
   │       └─> Envoi au serveur / Send to server
   │
   └─> Serveur renvoie PLAYER_UPDATE / Server sends back PLAYER_UPDATE
       │
       └─> _handle_server_message()
           │
           ├─> self.window.rotation = tuple(player_data["rotation"])  ← ✅ NOUVEAU / NEW
           │
           └─> self.window.local_player_cube.update_rotation(self.window.rotation)  ← ✅ NOUVEAU / NEW
```

## Conclusion

**Résumé FR**: Cette correction garantit que la rotation du joueur est toujours synchronisée entre la vue du joueur et son cube visible par les caméras et autres joueurs. Le problème de "l'utilisateur qui tourne mais qu'on ne voit pas" est maintenant résolu.

**Summary EN**: This fix ensures that player rotation is always synchronized between the player's view and their visible cube as seen by cameras and other players. The problem of "the user rotating but not being visible" is now resolved.

---

**Date**: 2024
**Auteur / Author**: GitHub Copilot Agent
**Type**: Correction de bug / Bug fix
**Priorité / Priority**: Haute / High
**Impact**: Fonctionnalité critique restaurée / Critical functionality restored
