# Sélection de Type de Caméra avec la Molette de Souris

## Vue d'ensemble

Cette fonctionnalité permet aux utilisateurs de choisir différents types de caméra en utilisant la molette de la souris lorsque le bloc caméra est sélectionné.

## Types de Caméra Disponibles

1. **Statique** - Caméra fixe qui ne bouge pas
2. **Rotative** - Caméra qui tourne automatiquement
3. **Poursuite** - Caméra qui suit les joueurs
4. **Grand Angle** - Caméra avec un champ de vision élargi
5. **Zoom** - Caméra avec capacité de zoom

## Utilisation

### Sélection du Bloc Caméra
1. Utilisez la molette de la souris pour naviguer dans l'inventaire
2. Sélectionnez le bloc "camera"
3. Le type de caméra actuel s'affiche dans l'interface

### Changement du Type de Caméra
1. Assurez-vous que le bloc caméra est sélectionné
2. Maintenez la touche **Ctrl** enfoncée
3. Utilisez la molette de la souris :
   - **Molette vers le haut** : Type de caméra suivant
   - **Molette vers le bas** : Type de caméra précédent

### Interface Utilisateur
- Le type de bloc actuel est affiché en permanence en haut à gauche
- Quand un bloc caméra est sélectionné, le type de caméra apparaît entre parenthèses
- Un message d'aide "Ctrl+Molette pour changer le type" s'affiche lors de la sélection
- Les changements de type génèrent des messages de confirmation

## Exemple d'Utilisation

```
1. Bloc sélectionné: camera (Type: Statique) - Ctrl+Molette pour changer le type
2. [Ctrl + Molette vers le haut]
3. Type de caméra: Rotative
4. [Ctrl + Molette vers le haut]
5. Type de caméra: Poursuite
```

## Intégration avec le Système de Caméra

Le type de caméra sélectionné est stocké dans `window.current_camera_type` et peut être utilisé par :
- Le gestionnaire de caméra lors du placement de blocs
- Le système de rendu pour ajuster le comportement de la caméra
- L'API FastAPI pour configurer les serveurs de caméra

## Code Technique

### Nouvelles Classes dans `protocol.py`
```python
class CameraType:
    STATIC = "static"
    ROTATING = "rotating" 
    TRACKING = "tracking"
    WIDE_ANGLE = "wide_angle"
    ZOOM = "zoom"
```

### Variables ajoutées dans `MinecraftWindow`
```python
self.camera_types = [CameraType.STATIC, CameraType.ROTATING, CameraType.TRACKING, CameraType.WIDE_ANGLE, CameraType.ZOOM]
self.current_camera_type = self.camera_types[0]
```

### Gestionnaire d'événements modifié
- `on_mouse_scroll()` - Détecte Ctrl+Molette pour sélection type caméra
- `on_key_press()` / `on_key_release()` - Suit l'état de la touche Ctrl
- `update_block_display()` - Affiche le type de caméra dans l'UI