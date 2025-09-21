#!/usr/bin/env python3
"""
Démonstration de la détection de collision basée sur l'IOU (Intersection over Union).

Ce script montre comment utiliser la nouvelle fonction compute_iou et son intégration
dans la logique de collision du projet cv_minecraft.

Exemples d'utilisation:
- Fonction compute_iou pour calculer l'IOU entre bounding boxes
- Intégration dans UnifiedCollisionManager avec la méthode check_block_collision_iou
- Utilisation de check_collision avec use_iou=True
- API simplifiée avec unified_check_collision_iou
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    compute_iou, check_collision_iou, UnifiedCollisionManager,
    unified_check_collision_iou, get_collision_iou_value,
    PLAYER_WIDTH, PLAYER_HEIGHT
)

def demo_compute_iou_function():
    """Démonstration de la fonction compute_iou."""
    print("🔹 Démonstration de la fonction compute_iou")
    print("=" * 60)
    
    # Exemple 1: Pas d'intersection
    print("\n📐 Exemple 1: Pas d'intersection")
    player_bbox = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    block_bbox = ((2.0, 0.0, 0.0), (3.0, 1.0, 1.0))
    iou = compute_iou(player_bbox, block_bbox)
    print(f"   Joueur: (0,0,0) à (1,1,1)")
    print(f"   Bloc:   (2,0,0) à (3,1,1)")
    print(f"   IOU: {iou:.6f} → {'Collision' if iou > 0 else 'Pas de collision'}")
    
    # Exemple 2: Intersection partielle
    print("\n📐 Exemple 2: Intersection partielle")
    player_bbox = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    block_bbox = ((0.5, 0.0, 0.0), (1.5, 1.0, 1.0))
    iou = compute_iou(player_bbox, block_bbox)
    print(f"   Joueur: (0,0,0) à (1,1,1)")
    print(f"   Bloc:   (0.5,0,0) à (1.5,1,1)")
    print(f"   IOU: {iou:.6f} → {'Collision' if iou > 0 else 'Pas de collision'}")
    
    # Exemple 3: Intersection complète
    print("\n📐 Exemple 3: Intersection complète")
    player_bbox = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    block_bbox = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    iou = compute_iou(player_bbox, block_bbox)
    print(f"   Joueur: (0,0,0) à (1,1,1)")
    print(f"   Bloc:   (0,0,0) à (1,1,1)")
    print(f"   IOU: {iou:.6f} → {'Collision' if iou > 0 else 'Pas de collision'}")

def demo_check_collision_iou():
    """Démonstration de check_collision_iou."""
    print("\n🔹 Démonstration de check_collision_iou")
    print("=" * 60)
    
    # Bloc de référence: (0,0,0) qui va de (0,0,0) à (1,1,1)
    block_pos = (0, 0, 0)
    
    test_positions = [
        (0.5, 0.5, 0.5),    # Centre du bloc
        (0.0, 0.5, 0.5),    # Bord gauche du bloc
        (1.0, 0.5, 0.5),    # Bord droit du bloc
        (0.5, 0.0, 0.5),    # Bord bas du bloc
        (0.5, 1.0, 0.5),    # Bord haut du bloc
        (2.0, 0.5, 0.5),    # Loin du bloc
    ]
    
    print(f"\n   Test avec bloc à la position {block_pos}")
    print(f"   Dimensions joueur: {PLAYER_WIDTH}x{PLAYER_WIDTH}x{PLAYER_HEIGHT}")
    
    for i, pos in enumerate(test_positions, 1):
        iou = check_collision_iou(pos, block_pos)
        status = "COLLISION" if iou > 0 else "LIBRE"
        print(f"   Position {i}: {pos} → IOU: {iou:.6f} → {status}")

def demo_unified_collision_manager():
    """Démonstration avec UnifiedCollisionManager."""
    print("\n🔹 Démonstration avec UnifiedCollisionManager")
    print("=" * 60)
    
    # Créer un monde simple
    world = {
        (0, 0, 0): 'stone',
        (2, 0, 0): 'grass',
        (0, 2, 0): 'dirt',
        (1, 1, 1): 'sand',
    }
    
    manager = UnifiedCollisionManager(world)
    
    print("\n   Monde créé avec blocs:")
    for pos, block_type in world.items():
        print(f"     {pos}: {block_type}")
    
    test_positions = [
        (0.5, 0.5, 0.5),    # Dans le bloc stone
        (1.5, 0.5, 0.5),    # Entre stone et grass
        (2.5, 0.5, 0.5),    # Dans le bloc grass
        (5.0, 5.0, 5.0),    # Loin de tout
    ]
    
    print("\n   Comparaison AABB vs IOU:")
    for i, pos in enumerate(test_positions, 1):
        aabb_result = manager.check_block_collision(pos)
        iou_result = manager.check_block_collision_iou(pos)
        combined_result = manager.check_collision(pos, use_iou=True)
        
        print(f"   Position {i}: {pos}")
        print(f"     AABB: {'COLLISION' if aabb_result else 'LIBRE'}")
        print(f"     IOU:  {'COLLISION' if iou_result else 'LIBRE'}")
        print(f"     Combiné (IOU): {'COLLISION' if combined_result else 'LIBRE'}")

def demo_api_functions():
    """Démonstration des fonctions API simplifiées."""
    print("\n🔹 Démonstration des fonctions API simplifiées")
    print("=" * 60)
    
    world = {
        (0, 0, 0): 'stone',
        (1, 0, 0): 'grass',
    }
    
    test_positions = [
        (0.5, 0.5, 0.5),    # Dans le stone
        (1.5, 0.5, 0.5),    # Dans le grass
        (3.0, 0.5, 0.5),    # Libre
    ]
    
    print("\n   Tests avec API simplifiée:")
    for i, pos in enumerate(test_positions, 1):
        # Test avec unified_check_collision_iou
        collision = unified_check_collision_iou(pos, world)
        
        # Test avec get_collision_iou_value pour chaque bloc
        stone_iou = get_collision_iou_value(pos, (0, 0, 0))
        grass_iou = get_collision_iou_value(pos, (1, 0, 0))
        
        print(f"   Position {i}: {pos}")
        print(f"     unified_check_collision_iou: {'COLLISION' if collision else 'LIBRE'}")
        print(f"     IOU vs stone (0,0,0): {stone_iou:.6f}")
        print(f"     IOU vs grass (1,0,0): {grass_iou:.6f}")

def demo_edge_corner_detection():
    """Démonstration de la détection sur arêtes et coins."""
    print("\n🔹 Démonstration: Détection sur arêtes et coins")
    print("=" * 60)
    
    world = {(0, 0, 0): 'stone'}
    
    # Positions sur les arêtes et coins
    edge_corner_positions = [
        ("Centre", (0.5, 0.5, 0.5)),
        ("Arête gauche", (0.0, 0.5, 0.5)),
        ("Arête droite", (1.0, 0.5, 0.5)),
        ("Coin bas-gauche-avant", (0.0, 0.0, 0.0)),
        ("Coin haut-droit-arrière", (1.0, 1.0, 1.0)),
        ("Près du coin (légèrement extérieur)", (1.1, 1.1, 1.1)),
    ]
    
    print(f"\n   Test avec bloc stone à (0,0,0)")
    print(f"   Requirement: Détection même sur arêtes et coins")
    
    for description, pos in edge_corner_positions:
        collision = unified_check_collision_iou(pos, world)
        iou_value = get_collision_iou_value(pos, (0, 0, 0))
        
        print(f"   {description}:")
        print(f"     Position: {pos}")
        print(f"     IOU: {iou_value:.6f}")
        print(f"     Résultat: {'✅ COLLISION DÉTECTÉE' if collision else '❌ Pas de collision'}")

def main():
    """Fonction principale de démonstration."""
    print("🎮 DÉMONSTRATION: DÉTECTION DE COLLISION IOU")
    print("Implémentation d'une vérification de collision basée sur l'IOU")
    print("=" * 80)
    
    print("\n📋 Spécifications implémentées:")
    print("✅ Fonction compute_iou pour calculer l'Intersection over Union")
    print("✅ Retourne valeur non nulle si volumes se chevauchent")
    print("✅ Intégration dans minecraft_physics.py")
    print("✅ Remplace/complète la détection AABB existante")
    print("✅ Détection sur arêtes et coins")
    print("✅ Exemple d'utilisation: si IOU > 0, collision détectée")
    
    # Exécuter les démonstrations
    demo_compute_iou_function()
    demo_check_collision_iou()
    demo_unified_collision_manager()
    demo_api_functions()
    demo_edge_corner_detection()
    
    print("\n" + "=" * 80)
    print("🎉 DÉMONSTRATION TERMINÉE")
    print("\n💡 Utilisation recommandée:")
    print("   # Méthode simple")
    print("   collision = unified_check_collision_iou(position, world)")
    print("   if collision:")
    print("       print('Collision détectée!')")
    print()
    print("   # Méthode avec valeur IOU")
    print("   iou = get_collision_iou_value(player_pos, block_pos)")
    print("   if iou > 0:")
    print("       print(f'Collision avec IOU = {iou:.6f}')")
    print()
    print("   # Intégration avec UnifiedCollisionManager")
    print("   manager = UnifiedCollisionManager(world)")
    print("   collision = manager.check_collision(position, use_iou=True)")

if __name__ == "__main__":
    main()