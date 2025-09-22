#!/usr/bin/env python3
"""
Test pour investiguer l'inconsistance détectée dans la collision detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def investigate_collision_detection_bug():
    """Investigate the collision detection inconsistency."""
    print("🔍 Investigation de l'Inconsistance de Détection de Collision")
    print("=" * 70)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Position problématique détectée: (4.5, 10.5, 5.5)
    pos = (4.5, 10.5, 5.5)
    px, py, pz = pos
    
    print(f"Position test: {pos}")
    print(f"Bloc: (5, 10, 5) → limites [5.0-6.0, 10.0-11.0, 5.0-6.0]")
    print(f"Joueur: largeur {PLAYER_WIDTH}, hauteur {PLAYER_HEIGHT}")
    print()
    
    # Calculer bounding box du joueur
    player_half_width = PLAYER_WIDTH / 2  # 0.5
    player_min_x = px - player_half_width  # 4.5 - 0.5 = 4.0
    player_max_x = px + player_half_width  # 4.5 + 0.5 = 5.0  
    player_min_y = py                      # 10.5
    player_max_y = py + PLAYER_HEIGHT      # 10.5 + 1.0 = 11.5
    player_min_z = pz - player_half_width  # 5.5 - 0.5 = 5.0
    player_max_z = pz + player_half_width  # 5.5 + 0.5 = 6.0
    
    print("Bounding Box Joueur:")
    print(f"  X: [{player_min_x} - {player_max_x}]")
    print(f"  Y: [{player_min_y} - {player_max_y}]") 
    print(f"  Z: [{player_min_z} - {player_max_z}]")
    print()
    
    # Bloc boundaries  
    block_min_x, block_max_x = 5.0, 6.0
    block_min_y, block_max_y = 10.0, 11.0
    block_min_z, block_max_z = 5.0, 6.0
    
    print("Bounding Box Bloc:")
    print(f"  X: [{block_min_x} - {block_max_x}]")
    print(f"  Y: [{block_min_y} - {block_max_y}]")
    print(f"  Z: [{block_min_z} - {block_max_z}]")
    print()
    
    # Test d'intersection AABB manuel
    x_overlap = player_min_x < block_max_x and player_max_x >= block_min_x
    y_overlap = player_min_y < block_max_y and player_max_y >= block_min_y 
    z_overlap = player_min_z < block_max_z and player_max_z >= block_min_z
    
    print("Test d'intersection manuel:")
    print(f"  X overlap: {player_min_x} < {block_max_x} and {player_max_x} >= {block_min_x} = {x_overlap}")
    print(f"  Y overlap: {player_min_y} < {block_max_y} and {player_max_y} >= {block_min_y} = {y_overlap}")
    print(f"  Z overlap: {player_min_z} < {block_max_z} and {player_max_z} >= {block_min_z} = {z_overlap}")
    
    manual_collision = x_overlap and y_overlap and z_overlap
    print(f"  → Collision manuelle: {manual_collision}")
    print()
    
    # Test avec la méthode du manager
    detected_collision = manager.check_block_collision(pos)
    print(f"Manager détection: {detected_collision}")
    print()
    
    # Analyser pourquoi il y a une différence
    print("🔍 ANALYSE DE L'ÉCART:")
    
    # Le problème pourrait être dans les comparaisons avec >= vs >
    # Vérifions les valeurs exactes
    print(f"player_max_x = {player_max_x}")
    print(f"block_min_x = {block_min_x}")
    print(f"player_max_x >= block_min_x: {player_max_x >= block_min_x}")
    print(f"player_max_x > block_min_x: {player_max_x > block_min_x}")
    print()
    
    print(f"player_max_z = {player_max_z}")
    print(f"block_min_z = {block_min_z}")
    print(f"player_max_z >= block_min_z: {player_max_z >= block_min_z}")
    print(f"player_max_z > block_min_z: {player_max_z > block_min_z}")
    print()
    
    # PROBLÈME PROBABLE: la position (4.5, 10.5, 5.5) place le joueur exactement
    # sur les limites du bloc. Le joueur va de x=4.0 à x=5.0 et z=5.0 à z=6.0
    # Le bloc va de x=5.0 à x=6.0 et z=5.0 à z=6.0
    # Donc le joueur touche exactement les faces du bloc!
    
    if player_max_x == block_min_x:
        print("⚠️  Le joueur touche exactement la face X du bloc!")
    if player_max_z == block_min_z:
        print("⚠️  Le joueur touche exactement la face Z du bloc!")
    
    # Dans Minecraft, toucher exactement la face devrait-il être une collision ?
    # Généralement OUI, car on ne peut pas "coller" parfaitement à un bloc
    
    print()
    print("🎯 CONCLUSION:")
    print("La position (4.5, 10.5, 5.5) place le joueur de façon que:")
    print("- Son bord droit (x=5.0) touche exactement la face gauche du bloc (x=5.0)")
    print("- Son bord arrière (z=6.0) touche exactement la face arrière du bloc (z=6.0)")
    print("Cette situation est ambiguë et dépend de l'implémentation des comparaisons.")
    
    return detected_collision, manual_collision

def test_boundary_conditions():
    """Test various boundary conditions to understand the collision detection behavior."""
    print("\n🎯 Test des Conditions de Frontière")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Test positions around the block boundary
    test_positions = [
        (4.49, 10.5, 5.5),  # Just outside X boundary
        (4.5, 10.5, 5.5),   # Exactly on X boundary
        (4.51, 10.5, 5.5),  # Just inside X boundary
        
        (5.5, 10.5, 4.49),  # Just outside Z boundary  
        (5.5, 10.5, 4.5),   # Exactly on Z boundary
        (5.5, 10.5, 4.51),  # Just inside Z boundary
    ]
    
    for pos in test_positions:
        collision = manager.check_block_collision(pos)
        px, py, pz = pos
        
        # Calculate player bounds
        player_min_x = px - 0.5
        player_max_x = px + 0.5
        player_min_z = pz - 0.5
        player_max_z = pz + 0.5
        
        print(f"Position {pos}: collision = {collision}")
        print(f"  Player X: [{player_min_x} - {player_max_x}]")
        print(f"  Player Z: [{player_min_z} - {player_max_z}]")
        
        # Check if any player edge is inside block
        x_inside = player_max_x > 5.0
        z_inside = player_max_z > 5.0
        
        if x_inside or z_inside:
            print(f"  Player penetrates block: X={x_inside}, Z={z_inside}")
        else:
            print(f"  Player outside block")
        print()

def main():
    """Main function to investigate collision detection."""
    detected, manual = investigate_collision_detection_bug()
    test_boundary_conditions()
    
    print("=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    
    if detected != manual:
        print("❌ INCONSISTANCE CONFIRMÉE dans la détection de collision")
        print(f"   Manager détecte: {detected}")
        print(f"   Calcul manuel: {manual}")
        print()
        print("🔧 CAUSE PROBABLE:")
        print("   Les comparaisons de frontière (>= vs >) ne sont pas cohérentes")
        print("   entre le calcul manuel et l'implémentation du manager.")
        return False
    else:
        print("✅ Détection cohérente")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)