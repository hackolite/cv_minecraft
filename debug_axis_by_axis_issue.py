#!/usr/bin/env python3
"""
Debug detaillé du problème de collision
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def analyze_collision_scenario():
    """Analyser précisément le scénario de collision."""
    print("🔍 Analyse Détaillée du Scénario de Collision")
    print("=" * 60)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Scénario problématique
    start = (4.8, 10.5, 4.3)
    end = (5.2, 10.5, 5.7)
    
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Block: (5, 10, 5) → bounds [5.0-6.0, 10.0-11.0, 5.0-6.0]")
    print()
    
    # Analyser pourquoi le système actuel permet la pénétration
    print("🎯 ANALYSE DU PROBLÈME:")
    print()
    
    # 1. Position de départ
    sx, sy, sz = start
    start_player_x_bounds = (sx - 0.5, sx + 0.5)  # (4.3, 5.3)
    start_player_z_bounds = (sz - 0.5, sz + 0.5)  # (3.8, 4.8)
    
    print(f"1. Position de départ {start}:")
    print(f"   Player X bounds: {start_player_x_bounds}")
    print(f"   Player Z bounds: {start_player_z_bounds}")
    print(f"   Block X bounds: (5.0, 6.0)")
    print(f"   Block Z bounds: (5.0, 6.0)")
    
    start_x_overlap = start_player_x_bounds[0] < 6.0 and start_player_x_bounds[1] > 5.0
    start_z_overlap = start_player_z_bounds[0] < 6.0 and start_player_z_bounds[1] > 5.0
    print(f"   X overlap: {start_x_overlap}")
    print(f"   Z overlap: {start_z_overlap}")
    print(f"   → Start collision: {start_x_overlap and start_z_overlap}")
    print()
    
    # 2. Position de fin
    ex, ey, ez = end
    end_player_x_bounds = (ex - 0.5, ex + 0.5)  # (4.7, 5.7)
    end_player_z_bounds = (ez - 0.5, ez + 0.5)  # (5.2, 6.2)
    
    print(f"2. Position de fin {end}:")
    print(f"   Player X bounds: {end_player_x_bounds}")
    print(f"   Player Z bounds: {end_player_z_bounds}")
    
    end_x_overlap = end_player_x_bounds[0] < 6.0 and end_player_x_bounds[1] > 5.0
    end_z_overlap = end_player_z_bounds[0] < 6.0 and end_player_z_bounds[1] > 5.0
    print(f"   X overlap: {end_x_overlap}")
    print(f"   Z overlap: {end_z_overlap}")
    print(f"   → End collision: {end_x_overlap and end_z_overlap}")
    print()
    
    # 3. Mouvement axis-by-axis actuel
    print("3. Résolution axis-by-axis actuelle:")
    print("   Phase 1: X movement (4.8 → 5.2) avec Y=10.5, Z=4.3")
    
    # À Z=4.3, les bounds du joueur en Z sont (3.8, 4.8)
    # Le bloc est à Z=(5.0, 6.0)
    # Pas d'overlap en Z → pas de collision détectée pour le mouvement X
    z_at_x_movement = 4.3
    player_z_bounds_at_x = (z_at_x_movement - 0.5, z_at_x_movement + 0.5)  # (3.8, 4.8)
    x_phase_z_overlap = player_z_bounds_at_x[0] < 6.0 and player_z_bounds_at_x[1] > 5.0
    
    print(f"   Player Z bounds during X movement: {player_z_bounds_at_x}")
    print(f"   Z overlap during X movement: {x_phase_z_overlap}")
    print(f"   → X movement allowed: {not x_phase_z_overlap}")
    
    if not x_phase_z_overlap:
        print(f"   ✅ X movement 4.8 → 5.2 PERMIS (aucun overlap Z)")
    
    print()
    print("   Phase 2: Z movement (4.3 → 5.7) avec X=5.2, Y=10.5")
    
    # À X=5.2, les bounds du joueur en X sont (4.7, 5.7)
    # Le bloc est à X=(5.0, 6.0)
    # Il y a overlap en X → collision détectée pour le mouvement Z
    x_at_z_movement = 5.2
    player_x_bounds_at_z = (x_at_z_movement - 0.5, x_at_z_movement + 0.5)  # (4.7, 5.7)
    z_phase_x_overlap = player_x_bounds_at_z[0] < 6.0 and player_x_bounds_at_z[1] > 5.0
    
    print(f"   Player X bounds during Z movement: {player_x_bounds_at_z}")
    print(f"   X overlap during Z movement: {z_phase_x_overlap}")
    print(f"   → Z movement blocked: {z_phase_x_overlap}")
    
    if z_phase_x_overlap:
        # Z movement should be snapped
        safe_z = 5.0 - 0.5  # 4.5
        print(f"   🚫 Z movement 4.3 → 5.7 BLOQUÉ, snappé à Z={safe_z}")
    
    print()
    print("🚨 RÉSULTAT PROBLÉMATIQUE:")
    print(f"   Position finale: (5.2, 10.5, 4.5)")
    print(f"   Player X bounds: (4.7, 5.7) → pénètre le bloc de 0.7")
    print(f"   Player Z bounds: (4.0, 5.0) → touche juste la limite")
    print()
    print("🔧 PROBLÈME IDENTIFIÉ:")
    print("   Le système axis-by-axis permet au joueur de bouger en X")
    print("   quand il n'y a pas encore de collision en Z, mais cela")
    print("   crée une pénétration partielle une fois que Z est ajusté.")
    
    return True

def main():
    analyze_collision_scenario()

if __name__ == "__main__":
    main()