#!/usr/bin/env python3
"""
Demonstration: Server-Side Collision Detection Implementation

This script demonstrates the server-side collision detection system as specified:

1️⃣ Principe général:
- Le monde est une grille 3D de voxels (chaque voxel = un bloc de 1×1×1)  
- Chaque voxel peut être vide ou solide
- On teste seulement les blocs autour de la position (voisins immédiats)

2️⃣ Bounding box du joueur: largeur ~0.6, profondeur ~0.6, hauteur ~1.8

3️⃣ Formules mathématiques exactes implémentées:
- xmin = floor(px - largeur/2)
- xmax = floor(px + largeur/2)
- ymin = floor(py)  
- ymax = floor(py + hauteur)
- zmin = floor(pz - profondeur/2)
- zmax = floor(pz + profondeur/2)

4️⃣ Déplacement par axe (X, Y, Z séparément) pour éviter de rester coincé
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT


def demonstrate_server_side_collision():
    """Demonstrate server-side collision detection in action."""
    print("🎮 Demonstration: Server-Side Collision Detection")
    print("=" * 60)
    print()
    
    print("1️⃣ Principe général:")
    print("   • Le monde est une grille 3D de voxels (1×1×1)")
    print("   • Chaque voxel peut être vide ou solide")
    print("   • Test seulement les blocs voisins (performance optimisée)")
    print()
    
    # Create a test world with voxels
    print("🌍 Création du monde (grille 3D de voxels):")
    world = {}
    
    # Ground plane
    for x in range(10, 15):
        for z in range(10, 15):
            world[(x, 10, z)] = 'grass'
    
    # Some walls and obstacles
    obstacles = [
        (12, 11, 12), (12, 12, 12),  # Vertical wall
        (13, 11, 10), (13, 11, 11),  # Another wall section
        (10, 11, 13), (11, 11, 13),  # Horizontal wall
    ]
    
    for pos in obstacles:
        world[pos] = 'stone'
    
    print(f"   • {len(world)} voxels créés dans le monde")
    print(f"   • Sol en herbe: Y=10")
    print(f"   • Obstacles en pierre: Y=11-12")
    print()
    
    manager = UnifiedCollisionManager(world)
    
    print("2️⃣ Configuration du joueur:")
    print(f"   • Largeur: {PLAYER_WIDTH} blocs")
    print(f"   • Profondeur: {PLAYER_WIDTH} blocs")
    print(f"   • Hauteur: {PLAYER_HEIGHT} blocs")
    print(f"   • Bounding box AABB: {PLAYER_WIDTH}×{PLAYER_WIDTH}×{PLAYER_HEIGHT}")
    print()
    
    print("3️⃣ Test des formules mathématiques:")
    
    # Test case 1: Player in open space
    player_pos = (11.5, 11.5, 11.5)
    px, py, pz = player_pos
    
    # Calculate voxel bounds using exact formulas
    largeur = PLAYER_WIDTH
    hauteur = PLAYER_HEIGHT
    profondeur = PLAYER_WIDTH
    
    xmin = int(math.floor(px - largeur / 2))
    xmax = int(math.floor(px + largeur / 2))
    ymin = int(math.floor(py))
    ymax = int(math.floor(py + hauteur))
    zmin = int(math.floor(pz - profondeur / 2))
    zmax = int(math.floor(pz + profondeur / 2))
    
    print(f"   Position joueur: ({px}, {py}, {pz})")
    print(f"   Formules appliquées:")
    print(f"     xmin = floor({px} - {largeur}/2) = {xmin}")
    print(f"     xmax = floor({px} + {largeur}/2) = {xmax}")
    print(f"     ymin = floor({py}) = {ymin}")
    print(f"     ymax = floor({py} + {hauteur}) = {ymax}")
    print(f"     zmin = floor({pz} - {profondeur}/2) = {zmin}")
    print(f"     zmax = floor({pz} + {profondeur}/2) = {zmax}")
    print()
    
    # Test collision
    collision = manager.check_block_collision(player_pos)
    voxels_tested = []
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            for z in range(zmin, zmax + 1):
                voxels_tested.append((x, y, z))
    
    print(f"   Voxels testés: {len(voxels_tested)} (seulement les voisins)")
    print(f"   Voxels: {voxels_tested}")
    print(f"   Collision détectée: {'OUI' if collision else 'NON'}")
    print()
    
    print("4️⃣ Test du déplacement par axe:")
    
    # Test diagonal movement that should be resolved per-axis
    test_scenarios = [
        {
            "name": "Mouvement libre",
            "start": (11.0, 11.5, 11.0),
            "target": (11.5, 11.5, 11.5),
            "description": "Pas d'obstacles"
        },
        {
            "name": "Collision sur axe X",
            "start": (11.5, 11.5, 12.3),
            "target": (12.5, 11.5, 12.7),
            "description": "Mur bloque X, Z autorisé"
        },
        {
            "name": "Collision multiple",
            "start": (12.3, 11.5, 12.3),
            "target": (13.2, 11.5, 13.2),
            "description": "Obstacles multiples"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"   Test {i}: {scenario['name']}")
        print(f"   {scenario['description']}")
        
        start_pos = scenario['start']
        target_pos = scenario['target']
        
        print(f"   Position initiale: {start_pos}")
        print(f"   Position cible: {target_pos}")
        
        # Use server-side collision resolution
        safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        
        print(f"   Position résolue: {safe_pos}")
        print(f"   Résolution par axe:")
        print(f"     X: {'BLOQUÉ' if collision_info['x'] else 'AUTORISÉ'}")
        print(f"     Y: {'BLOQUÉ' if collision_info['y'] else 'AUTORISÉ'}")  
        print(f"     Z: {'BLOQUÉ' if collision_info['z'] else 'AUTORISÉ'}")
        
        if any(collision_info[axis] for axis in ['x', 'y', 'z']):
            blocked_axes = [axis.upper() for axis in ['x', 'y', 'z'] if collision_info[axis]]
            print(f"   → Vitesse réinitialisée sur: {', '.join(blocked_axes)}")
        else:
            print(f"   → Mouvement libre, vitesse conservée")
        print()
    
    print("🎉 DEMONSTRATION TERMINÉE")
    print()
    print("✅ Collision côté serveur implémentée selon les spécifications:")
    print("  • Grille 3D de voxels (1×1×1)")
    print("  • AABB du joueur (0.6×0.6×1.8)")
    print("  • Formules mathématiques exactes")
    print("  • Test des voxels voisins uniquement")
    print("  • Résolution par axe (X, Y, Z séparément)")
    print("  • Réinitialisation de vitesse par axe bloqué")
    print()
    print("💡 L'idée principale: éviter de parcourir tout le monde,")
    print("   tester seulement les blocs pertinents pour la collision.")


def demonstrate_performance_optimization():
    """Demonstrate the performance optimization of testing only neighboring voxels."""
    print("\n🚀 Demonstration: Optimisation de Performance")
    print("=" * 50)
    
    # Create a large world
    large_world = {}
    
    # Add many distant blocks
    for x in range(0, 100, 5):
        for y in range(0, 50, 5):
            for z in range(0, 100, 5):
                large_world[(x, y, z)] = 'stone'
    
    # Add one block near player
    large_world[(10, 11, 10)] = 'stone'
    
    print(f"🌍 Monde de test: {len(large_world)} blocs")
    print("   • Blocs distants: 99.9% du monde")
    print("   • Blocs proches: 1 bloc près du joueur")
    print()
    
    manager = UnifiedCollisionManager(large_world)
    
    # Test player near the one relevant block
    player_pos = (10.3, 11.5, 10.3)
    px, py, pz = player_pos
    
    # Calculate which voxels will be tested
    largeur, hauteur, profondeur = PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_WIDTH
    xmin = int(math.floor(px - largeur / 2))
    xmax = int(math.floor(px + largeur / 2))
    ymin = int(math.floor(py))
    ymax = int(math.floor(py + hauteur))
    zmin = int(math.floor(pz - profondeur / 2))
    zmax = int(math.floor(pz + profondeur / 2))
    
    voxels_in_range = 0
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            for z in range(zmin, zmax + 1):
                voxels_in_range += 1
    
    collision = manager.check_block_collision(player_pos)
    
    print(f"   Position joueur: {player_pos}")
    print(f"   Voxels testés: {voxels_in_range} / {len(large_world)}")
    print(f"   Pourcentage testé: {(voxels_in_range/len(large_world)*100):.3f}%")
    print(f"   Collision détectée: {'OUI' if collision else 'NON'}")
    print()
    print("✅ Optimisation: on ne teste que les voxels pertinents,")
    print("   pas l'ensemble du monde !")


if __name__ == "__main__":
    demonstrate_server_side_collision()
    demonstrate_performance_optimization()