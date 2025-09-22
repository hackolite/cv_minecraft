#!/usr/bin/env python3
"""
Test spécifique pour tester les fonctions de snapping par axe
et reproduire le bug de pénétration partielle en x+ ou z+
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_x_axis_snapping_detailed():
    """Test détaillé du snapping sur l'axe X pour détecter les problèmes."""
    print("🔧 Test Détaillé Snapping Axe X")
    print("=" * 50)
    
    # Créer un monde avec plusieurs blocs pour tester différents scénarios
    world = {
        (5, 10, 5): 'stone',
        (6, 10, 5): 'stone',
        (7, 10, 5): 'stone',
    }
    manager = UnifiedCollisionManager(world)
    
    print("Blocs: (5,10,5), (6,10,5), (7,10,5)")
    print(f"Joueur: largeur {PLAYER_WIDTH} (±{PLAYER_WIDTH/2})")
    print()
    
    # Tester les fonctions de snapping directement
    clearance = 0.01
    
    test_cases = [
        {
            'name': 'X+ vers bloc simple',
            'old_x': 4.0, 'new_x': 5.5, 'y': 10.5, 'z': 5.5,
            'expected_safe_x': 4.5 - clearance,  # Devrait s'arrêter juste avant le bloc
        },
        {
            'name': 'X+ mouvement petit',
            'old_x': 4.3, 'new_x': 4.7, 'y': 10.5, 'z': 5.5,
            'expected_safe_x': 4.5 - clearance,  # Devrait s'arrêter à la limite
        },
        {
            'name': 'X+ vers multiple blocs',
            'old_x': 4.0, 'new_x': 7.5, 'y': 10.5, 'z': 5.5,
            'expected_safe_x': 4.5 - clearance,  # Premier bloc rencontré
        },
        {
            'name': 'X+ déjà proche limite',
            'old_x': 4.48, 'new_x': 4.52, 'y': 10.5, 'z': 5.5,
            'expected_safe_x': 4.48,  # Ne devrait pas bouger car déjà trop proche
        }
    ]
    
    issues_found = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        print(f"   old_x: {test['old_x']}, new_x: {test['new_x']}")
        print(f"   y: {test['y']}, z: {test['z']}")
        
        # Appeler directement la fonction de snapping
        safe_x = manager._snap_to_safe_x_position(
            test['old_x'], test['new_x'], test['y'], test['z'], "test_player", clearance
        )
        
        print(f"   safe_x: {safe_x}")
        print(f"   expected: {test['expected_safe_x']}")
        
        # Vérifier si le résultat est acceptable
        if abs(safe_x - test['expected_safe_x']) > 0.001:
            print(f"   ⚠️  Résultat inattendu!")
            issues_found.append(f"Test {i}: safe_x={safe_x}, expected={test['expected_safe_x']}")
        
        # Vérifier que la position finale n'a pas de collision
        final_pos = (safe_x, test['y'], test['z'])
        collision = manager.check_block_collision(final_pos)
        if collision:
            print(f"   ❌ COLLISION à la position finale! {final_pos}")
            issues_found.append(f"Test {i}: Position finale {final_pos} en collision")
        else:
            print(f"   ✅ Position finale sans collision")
            
        # Analyser si il y a pénétration partielle
        player_right_edge = safe_x + PLAYER_WIDTH/2
        if player_right_edge > 5.0:  # 5.0 est la limite du premier bloc
            penetration = player_right_edge - 5.0
            print(f"   🚨 PÉNÉTRATION DÉTECTÉE: {penetration:.3f} blocs dans le bloc!")
            issues_found.append(f"Test {i}: Pénétration de {penetration:.3f}")
        
        print()
    
    return len(issues_found) == 0, issues_found

def test_z_axis_snapping_detailed():
    """Test détaillé du snapping sur l'axe Z pour détecter les problèmes."""
    print("🔧 Test Détaillé Snapping Axe Z")
    print("=" * 50)
    
    # Créer un monde avec plusieurs blocs pour tester différents scénarios
    world = {
        (5, 10, 5): 'stone',
        (5, 10, 6): 'stone', 
        (5, 10, 7): 'stone',
    }
    manager = UnifiedCollisionManager(world)
    
    print("Blocs: (5,10,5), (5,10,6), (5,10,7)")
    print(f"Joueur: largeur {PLAYER_WIDTH} (±{PLAYER_WIDTH/2})")
    print()
    
    # Tester les fonctions de snapping directement
    clearance = 0.01
    
    test_cases = [
        {
            'name': 'Z+ vers bloc simple',
            'x': 5.5, 'old_z': 4.0, 'new_z': 5.5, 'y': 10.5,
            'expected_safe_z': 4.5 - clearance,  # Devrait s'arrêter juste avant le bloc
        },
        {
            'name': 'Z+ mouvement petit',
            'x': 5.5, 'old_z': 4.3, 'new_z': 4.7, 'y': 10.5,
            'expected_safe_z': 4.5 - clearance,  # Devrait s'arrêter à la limite
        },
        {
            'name': 'Z+ vers multiple blocs',
            'x': 5.5, 'old_z': 4.0, 'new_z': 7.5, 'y': 10.5,
            'expected_safe_z': 4.5 - clearance,  # Premier bloc rencontré
        },
        {
            'name': 'Z+ déjà proche limite',
            'x': 5.5, 'old_z': 4.48, 'new_z': 4.52, 'y': 10.5,
            'expected_safe_z': 4.48,  # Ne devrait pas bouger car déjà trop proche
        }
    ]
    
    issues_found = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        print(f"   x: {test['x']}, old_z: {test['old_z']}, new_z: {test['new_z']}")
        print(f"   y: {test['y']}")
        
        # Appeler directement la fonction de snapping
        safe_z = manager._snap_to_safe_z_position(
            test['x'], test['old_z'], test['new_z'], test['y'], "test_player", clearance
        )
        
        print(f"   safe_z: {safe_z}")
        print(f"   expected: {test['expected_safe_z']}")
        
        # Vérifier si le résultat est acceptable
        if abs(safe_z - test['expected_safe_z']) > 0.001:
            print(f"   ⚠️  Résultat inattendu!")
            issues_found.append(f"Test {i}: safe_z={safe_z}, expected={test['expected_safe_z']}")
        
        # Vérifier que la position finale n'a pas de collision
        final_pos = (test['x'], test['y'], safe_z)
        collision = manager.check_block_collision(final_pos)
        if collision:
            print(f"   ❌ COLLISION à la position finale! {final_pos}")
            issues_found.append(f"Test {i}: Position finale {final_pos} en collision")
        else:
            print(f"   ✅ Position finale sans collision")
            
        # Analyser si il y a pénétration partielle
        player_front_edge = safe_z + PLAYER_WIDTH/2
        if player_front_edge > 5.0:  # 5.0 est la limite du premier bloc
            penetration = player_front_edge - 5.0
            print(f"   🚨 PÉNÉTRATION DÉTECTÉE: {penetration:.3f} blocs dans le bloc!")
            issues_found.append(f"Test {i}: Pénétration de {penetration:.3f}")
        
        print()
    
    return len(issues_found) == 0, issues_found

def test_bounding_box_vs_single_block_check():
    """Test pour vérifier si le problème vient de la différence entre bounding box et single block check."""
    print("📦 Test Bounding Box vs Single Block Check")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Position critique: joueur touchant juste le bloc
    critical_positions = [
        (4.5, 10.5, 5.5),   # Bord du bloc en X
        (5.5, 10.5, 4.5),   # Bord du bloc en Z  
        (4.5, 10.5, 4.5),   # Coin du bloc
        (5.5, 10.5, 5.5),   # Centre du bloc
    ]
    
    for pos in critical_positions:
        print(f"Position: {pos}")
        
        # Test avec la fonction check_block_collision (full bounding box)
        collision_bbox = manager.check_block_collision(pos)
        
        # Test avec _is_position_in_block (might be different)
        collision_simple = manager._is_position_in_block(pos)
        
        print(f"   check_block_collision: {collision_bbox}")
        print(f"   _is_position_in_block: {collision_simple}")
        
        if collision_bbox != collision_simple:
            print(f"   ⚠️  DIVERGENCE entre les méthodes de détection!")
            return False
        
        # Calculer manuellement si devrait être en collision
        px, py, pz = pos
        player_min_x = px - PLAYER_WIDTH/2
        player_max_x = px + PLAYER_WIDTH/2
        player_min_z = pz - PLAYER_WIDTH/2  
        player_max_z = pz + PLAYER_WIDTH/2
        
        # Bloc va de (5,10,5) à (6,11,6)
        block_intersects = (player_min_x < 6.0 and player_max_x > 5.0 and
                           py < 11.0 and py + PLAYER_HEIGHT > 10.0 and
                           player_min_z < 6.0 and player_max_z > 5.0)
        
        print(f"   Calcul manuel: {block_intersects}")
        
        if collision_bbox != block_intersects:
            print(f"   ❌ ERREUR: Détection != calcul manuel!")
            return False
        
        print()
    
    return True

def main():
    """Fonction principale pour tester les fonctions de snapping."""
    print("🔧 Test des Fonctions de Snapping par Axe")
    print("Objectif: Détecter les bugs de pénétration partielle en X+ et Z+")
    print()
    
    try:
        # Test bounding box consistency
        success1 = test_bounding_box_vs_single_block_check()
        
        # Test X axis snapping
        success2, issues_x = test_x_axis_snapping_detailed()
        
        # Test Z axis snapping  
        success3, issues_z = test_z_axis_snapping_detailed()
        
        overall_success = success1 and success2 and success3
        
        print("=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        if overall_success:
            print("✅ AUCUN PROBLÈME DÉTECTÉ")
            print("Les fonctions de snapping semblent fonctionner correctement")
        else:
            print("❌ PROBLÈMES DÉTECTÉS")
            
            if not success1:
                print("- Incohérence dans la détection de collision")
            
            if not success2:
                print("- Problèmes avec snapping axe X:")
                for issue in issues_x:
                    print(f"  • {issue}")
            
            if not success3:
                print("- Problèmes avec snapping axe Z:")
                for issue in issues_z:
                    print(f"  • {issue}")
        
        return overall_success
        
    except Exception as e:
        print(f"💥 Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)