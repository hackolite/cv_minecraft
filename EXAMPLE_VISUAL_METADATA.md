# Exemple Visuel - Métadonnées de Position x,y,z

## Démonstration

Voici un exemple concret de la capture et des métadonnées générées:

### Scénario

Une caméra se déplace progressivement:
- Frame 0: Position (10, 50, 10) - Position initiale
- Frame 1: Position (15, 52, 15) - Déplacement vers l'avant-droit
- Frame 2: Position (20, 54, 20) - Déplacement continu
- Frame 3: Position (25, 56, 25) - Position finale

### session_info.json

```json
{
  "duration_seconds": 0.27,
  "frame_count": 4,
  "average_fps": 14.90,
  "start_time": "2025-10-04T20:40:17.572587",
  "end_time": "2025-10-04T20:40:17.841190",
  "camera_info": {
    "camera_id": "demo_camera",
    "position": {
      "x": 25,
      "y": 56,
      "z": 25
    },
    "rotation": {
      "horizontal": 45,
      "vertical": 10
    }
  }
}
```

**Note**: La position dans `camera_info` est la position finale de la caméra.

### frames_metadata.json

```json
[
  {
    "frame_number": 0,
    "timestamp": 0.017,
    "width": 800,
    "height": 600,
    "camera_position": {
      "x": 10,
      "y": 50,
      "z": 10
    },
    "camera_rotation": {
      "horizontal": 45,
      "vertical": 10
    }
  },
  {
    "frame_number": 1,
    "timestamp": 0.107,
    "width": 800,
    "height": 600,
    "camera_position": {
      "x": 15,
      "y": 52,
      "z": 15
    },
    "camera_rotation": {
      "horizontal": 45,
      "vertical": 10
    }
  },
  {
    "frame_number": 2,
    "timestamp": 0.196,
    "width": 800,
    "height": 600,
    "camera_position": {
      "x": 20,
      "y": 54,
      "z": 20
    },
    "camera_rotation": {
      "horizontal": 45,
      "vertical": 10
    }
  },
  {
    "frame_number": 3,
    "timestamp": 0.269,
    "width": 800,
    "height": 600,
    "camera_position": {
      "x": 25,
      "y": 56,
      "z": 25
    },
    "camera_rotation": {
      "horizontal": 45,
      "vertical": 10
    }
  }
]
```

## Visualisation de la Trajectoire

```
Trajectoire de la caméra (vue de dessus):

Z
^
|
30 |
   |
25 |                           ● Frame 3 (25, 56, 25)
   |                          /
20 |                    ● Frame 2 (20, 54, 20)
   |                   /
15 |              ● Frame 1 (15, 52, 15)
   |             /
10 |        ● Frame 0 (10, 50, 10)
   |
 5 |
   |
 0 +----+----+----+----+----+----+----+----+----+-----> X
   0    5   10   15   20   25   30   35   40   45

Légende: ● = Position de la caméra à chaque frame
         / = Trajectoire de déplacement
```

## Utilisation des Métadonnées

### 1. Reconstruire la Trajectoire

```python
import json
from pathlib import Path

# Charger les métadonnées
with open("session_dir/frames_metadata.json") as f:
    frames = json.load(f)

# Extraire les positions
trajectory = []
for frame in frames:
    pos = frame['camera_position']
    trajectory.append((pos['x'], pos['y'], pos['z']))

print("Trajectoire:", trajectory)
# Output: [(10, 50, 10), (15, 52, 15), (20, 54, 20), (25, 56, 25)]
```

### 2. Analyser les Déplacements

```python
# Calculer la distance parcourue
import math

def distance_3d(p1, p2):
    return math.sqrt(
        (p2[0] - p1[0])**2 + 
        (p2[1] - p1[1])**2 + 
        (p2[2] - p1[2])**2
    )

total_distance = 0
for i in range(len(trajectory) - 1):
    dist = distance_3d(trajectory[i], trajectory[i+1])
    total_distance += dist
    print(f"Frame {i} -> {i+1}: {dist:.2f} unités")

print(f"Distance totale: {total_distance:.2f} unités")
```

Output:
```
Frame 0 -> 1: 7.35 unités
Frame 1 -> 2: 7.35 unités
Frame 2 -> 3: 7.35 unités
Distance totale: 22.04 unités
```

### 3. Synchroniser Plusieurs Caméras

```python
# Charger les métadonnées de plusieurs caméras
cameras = {
    "camera_1": json.load(open("cam1/frames_metadata.json")),
    "camera_2": json.load(open("cam2/frames_metadata.json")),
    "camera_3": json.load(open("cam3/frames_metadata.json")),
}

# Trouver les frames synchronisées (même timestamp approximatif)
def find_synchronized_frames(cameras, time_tolerance=0.1):
    sync_frames = []
    
    for i, frame1 in enumerate(cameras["camera_1"]):
        t1 = frame1['timestamp']
        
        # Chercher les frames correspondantes dans les autres caméras
        frame2 = min(cameras["camera_2"], 
                     key=lambda f: abs(f['timestamp'] - t1))
        frame3 = min(cameras["camera_3"], 
                     key=lambda f: abs(f['timestamp'] - t1))
        
        if (abs(frame2['timestamp'] - t1) < time_tolerance and
            abs(frame3['timestamp'] - t1) < time_tolerance):
            sync_frames.append({
                'timestamp': t1,
                'camera_1': frame1['camera_position'],
                'camera_2': frame2['camera_position'],
                'camera_3': frame3['camera_position']
            })
    
    return sync_frames
```

### 4. Débogage des Enregistrements

```python
# Vérifier si une caméra s'est déplacée de manière anormale
def check_abnormal_movement(frames, max_speed=10.0):
    for i in range(len(frames) - 1):
        dt = frames[i+1]['timestamp'] - frames[i]['timestamp']
        
        pos1 = frames[i]['camera_position']
        pos2 = frames[i+1]['camera_position']
        
        dist = distance_3d(
            (pos1['x'], pos1['y'], pos1['z']),
            (pos2['x'], pos2['y'], pos2['z'])
        )
        
        speed = dist / dt if dt > 0 else 0
        
        if speed > max_speed:
            print(f"⚠️  Mouvement anormal détecté!")
            print(f"   Frame {i} -> {i+1}")
            print(f"   Distance: {dist:.2f} unités en {dt:.3f}s")
            print(f"   Vitesse: {speed:.2f} unités/s")
            print(f"   Position 1: {pos1}")
            print(f"   Position 2: {pos2}")
```

## Avantages Pratiques

### 1. Reconstruction 3D

Les métadonnées permettent de reconstruire exactement ce que la caméra voyait:

```python
from OpenGL.GL import *

def render_from_metadata(frame_meta):
    # Positionner la caméra
    pos = frame_meta['camera_position']
    rot = frame_meta['camera_rotation']
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Appliquer rotation puis translation
    glRotatef(rot['horizontal'], 0, 1, 0)
    glRotatef(-rot['vertical'], 1, 0, 0)
    glTranslatef(-pos['x'], -pos['y'], -pos['z'])
    
    # Rendre le monde...
```

### 2. Analyse de Trajectoire

Pour l'intelligence artificielle ou l'analyse de comportement:

```python
def analyze_camera_behavior(frames):
    movements = []
    
    for i in range(len(frames) - 1):
        pos1 = frames[i]['camera_position']
        pos2 = frames[i+1]['camera_position']
        
        dx = pos2['x'] - pos1['x']
        dy = pos2['y'] - pos1['y']
        dz = pos2['z'] - pos1['z']
        
        movements.append({
            'frame': i,
            'direction': (dx, dy, dz),
            'vertical': dy > 0
        })
    
    # Analyser les patterns
    ascending = sum(1 for m in movements if m['vertical'])
    descending = len(movements) - ascending
    
    print(f"Montées: {ascending}, Descentes: {descending}")
```

### 3. Export vers Autres Outils

```python
# Export pour Blender, Unity, etc.
def export_to_blender(frames_file, output_file):
    with open(frames_file) as f:
        frames = json.load(f)
    
    # Format pour Blender (keyframes de caméra)
    blender_data = {
        'camera_keyframes': []
    }
    
    for frame in frames:
        pos = frame['camera_position']
        rot = frame['camera_rotation']
        
        blender_data['camera_keyframes'].append({
            'frame': frame['frame_number'],
            'location': [pos['x'], pos['y'], pos['z']],
            'rotation': [rot['horizontal'], rot['vertical'], 0]
        })
    
    with open(output_file, 'w') as f:
        json.dump(blender_data, f, indent=2)
```

## Conclusion

Les métadonnées de position x,y,z permettent:

✅ **Traçabilité**: Savoir exactement où était la caméra pour chaque frame  
✅ **Débogage**: Identifier les mouvements anormaux ou problèmes  
✅ **Reconstruction**: Recréer la vue 3D exacte de chaque frame  
✅ **Synchronisation**: Coordonner plusieurs caméras via les timestamps  
✅ **Analyse**: Étudier les trajectoires et comportements  
✅ **Export**: Intégrer avec d'autres outils (Blender, Unity, etc.)  
✅ **Intelligence**: Entraîner des modèles ML sur les trajectoires  

Les "enregistrements vidéo bizarres" peuvent maintenant être analysés en détail grâce aux métadonnées complètes!
