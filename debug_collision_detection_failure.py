#!/usr/bin/env python3
"""
Debug pour comprendre pourquoi la collision detection ne fonctionne pas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def debug_specific_failure():
    """Debug un cas d'échec spécifique."""
    print("🔍 Debug Cas d'Échec Spécifique")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Cas qui échoue: X+ depuis position libre
    start = (3.0, 10.5, 2.0)
    end = (6.0, 10.5, 2.0)
    
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Bloc: (5, 10, 5)")
    print()
    
    # Debug step by step
    print("1. Bounding box calculations:")
    
    # Player at start position
    start_x, start_y, start_z = start
    player_min_y_start = start_y
    player_max_y_start = start_y + PLAYER_HEIGHT
    player_min_z_start = start_z - PLAYER_WIDTH/2
    player_max_z_start = start_z + PLAYER_WIDTH/2
    
    print(f"   Start player Y: [{player_min_y_start} - {player_max_y_start}]")
    print(f"   Start player Z: [{player_min_z_start} - {player_max_z_start}]")
    
    # Player at end position
    end_x, end_y, end_z = end
    player_min_y_end = end_y
    player_max_y_end = end_y + PLAYER_HEIGHT
    player_min_z_end = end_z - PLAYER_WIDTH/2
    player_max_z_end = end_z + PLAYER_WIDTH/2
    
    print(f"   End player Y: [{player_min_y_end} - {player_max_y_end}]")
    print(f"   End player Z: [{player_min_z_end} - {player_max_z_end}]")
    
    # Block bounds
    print(f"   Block Y: [10.0 - 11.0]")
    print(f"   Block Z: [5.0 - 6.0]")
    print()
    
    print("2. Intersection checks:")
    
    # Y intersection
    y_intersects = player_min_y_end < 11.0 and player_max_y_end > 10.0
    print(f"   Y intersects: {y_intersects}")
    
    # Z intersection
    z_intersects = player_min_z_end < 6.0 and player_max_z_end > 5.0
    print(f"   Z intersects: {z_intersects}")
    
    print()
    print("3. Le problème:")
    print(f"   Player Z: [{player_min_z_end} - {player_max_z_end}] = [1.5 - 2.5]")
    print(f"   Block Z: [5.0 - 6.0]")
    print(f"   Pas d'intersection Z! Le joueur ne touche pas le bloc en Z.")
    print(f"   → Le système ne détecte pas de collision car pas d'overlap 3D.")
    print()
    
    # Test direct collision detection  
    safe_pos, collision_info = manager.resolve_collision(start, end)
    print(f"4. Résultat:")
    print(f"   Safe: {safe_pos}")
    print(f"   Collision: {collision_info}")
    
    # Le problème est que mon algorithme cherche seulement les blocs qui intersectent
    # avec la bounding box du joueur, mais dans ce cas le joueur ne touche pas le bloc
    # en Z, donc aucune collision n'est détectée.
    
    return True

def main():
    debug_specific_failure()

if __name__ == "__main__":
    main()