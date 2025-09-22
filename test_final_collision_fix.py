#!/usr/bin/env python3
"""
Test complet pour valider la correction du bug X+ Z+ comme spécifié dans le problème.

Ce test vérifie que:
1. Les mouvements en X+ sont strictement bloqués à la limite externe du bloc
2. Les mouvements en Z+ sont strictement bloqués à la limite externe du bloc  
3. La logique est parfaitement symétrique pour tous les axes
4. Aucune pénétration n'est possible même à grande vitesse
5. Le snapping est fait exactement comme spécifié: bloc_x - largeur/2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_x_plus_strict_blocking():
    """Test du blocage strict en X+ selon la spécification."""
    print("🔧 Test Blocage Strict X+")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc: (5, 10, 5) → face gauche à X=5.0")
    print(f"Limite théorique joueur: centre <= 4.5 (X=5.0 - {PLAYER_WIDTH/2})")
    print()
    
    # Test cases avec positions de départ valides (pas de collision initiale)
    test_cases = [
        {
            'name': 'X+ depuis position libre',
            'start': (3.0, 10.5, 2.0),  # Loin du bloc, pas de collision
            'end': (6.0, 10.5, 2.0),    # Mouvement X+ vers/à travers le bloc
            'expected_max_x': 4.5,      # bloc_x (5.0) - player_width/2 (0.5)
        },
        {
            'name': 'X+ petit mouvement vers limite',
            'start': (4.0, 10.5, 2.0),  # Position libre
            'end': (4.6, 10.5, 2.0),    # Petit mouvement qui dépasse la limite
            'expected_max_x': 4.5,
        },
        {
            'name': 'X+ mouvement autorisé jusqu\'à limite',
            'start': (4.0, 10.5, 2.0),  # Position libre
            'end': (4.5, 10.5, 2.0),    # Mouvement exactement jusqu\'à la limite
            'expected_max_x': 4.5,
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        # Vérifier que la position de départ est valide
        start_collision = manager.check_block_collision(start_pos)
        if start_collision:
            print(f"   ⚠️  Position de départ en collision: {start_pos}")
        
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        print(f"   Safe:  {safe_pos}")
        
        # Vérifier la limite X
        safe_x = safe_pos[0]
        if safe_x > test['expected_max_x'] + 0.001:  # Petite tolérance pour l'arithmétique flottante
            print(f"   ❌ ÉCHEC: X={safe_x:.3f} > limite {test['expected_max_x']}")
            all_passed = False
        else:
            print(f"   ✅ SUCCÈS: X={safe_x:.3f} <= limite {test['expected_max_x']}")
        
        # Vérifier qu'il n'y a pas de collision finale
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ Position finale en collision!")
            all_passed = False
        else:
            print(f"   ✅ Position finale sans collision")
        
        print()
    
    return all_passed

def test_z_plus_strict_blocking():
    """Test du blocage strict en Z+ selon la spécification."""
    print("🔧 Test Blocage Strict Z+")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc: (5, 10, 5) → face arrière à Z=5.0")
    print(f"Limite théorique joueur: centre <= 4.5 (Z=5.0 - {PLAYER_WIDTH/2})")
    print()
    
    # Test cases avec positions de départ valides
    test_cases = [
        {
            'name': 'Z+ depuis position libre',
            'start': (2.0, 10.5, 3.0),  # Loin du bloc, pas de collision
            'end': (2.0, 10.5, 6.0),    # Mouvement Z+ vers/à travers le bloc
            'expected_max_z': 4.5,      # bloc_z (5.0) - player_width/2 (0.5)
        },
        {
            'name': 'Z+ petit mouvement vers limite',
            'start': (2.0, 10.5, 4.0),  # Position libre
            'end': (2.0, 10.5, 4.6),    # Petit mouvement qui dépasse la limite
            'expected_max_z': 4.5,
        },
        {
            'name': 'Z+ mouvement autorisé jusqu\'à limite',
            'start': (2.0, 10.5, 4.0),  # Position libre
            'end': (2.0, 10.5, 4.5),    # Mouvement exactement jusqu\'à la limite
            'expected_max_z': 4.5,
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        # Vérifier que la position de départ est valide
        start_collision = manager.check_block_collision(start_pos)
        if start_collision:
            print(f"   ⚠️  Position de départ en collision: {start_pos}")
        
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        print(f"   Safe:  {safe_pos}")
        
        # Vérifier la limite Z
        safe_z = safe_pos[2]
        if safe_z > test['expected_max_z'] + 0.001:  # Petite tolérance pour l'arithmétique flottante
            print(f"   ❌ ÉCHEC: Z={safe_z:.3f} > limite {test['expected_max_z']}")
            all_passed = False
        else:
            print(f"   ✅ SUCCÈS: Z={safe_z:.3f} <= limite {test['expected_max_z']}")
        
        # Vérifier qu'il n'y a pas de collision finale
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ Position finale en collision!")
            all_passed = False
        else:
            print(f"   ✅ Position finale sans collision")
        
        print()
    
    return all_passed

def test_symmetric_logic_all_axes():
    """Test de la logique symétrique pour tous les axes."""
    print("🔧 Test Logique Symétrique Tous Axes")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("Bloc: (5, 10, 5) → limites [5.0-6.0, 10.0-11.0, 5.0-6.0]")
    print()
    
    # Test symétrie pour toutes les directions
    symmetric_tests = [
        {
            'name': 'X+ vers bloc',
            'start': (3.0, 5.0, 2.0),
            'end': (6.0, 5.0, 2.0),
            'expected_limit': 4.5,
            'axis': 0  # X axis
        },
        {
            'name': 'X- vers bloc', 
            'start': (7.0, 5.0, 2.0),
            'end': (4.0, 5.0, 2.0),
            'expected_limit': 6.5,  # bloc_x + 1 + player_width/2 = 6.0 + 0.5
            'axis': 0  # X axis
        },
        {
            'name': 'Z+ vers bloc',
            'start': (2.0, 5.0, 3.0),
            'end': (2.0, 5.0, 6.0),
            'expected_limit': 4.5,
            'axis': 2  # Z axis
        },
        {
            'name': 'Z- vers bloc',
            'start': (2.0, 5.0, 7.0),
            'end': (2.0, 5.0, 4.0),
            'expected_limit': 6.5,  # bloc_z + 1 + player_width/2 = 6.0 + 0.5
            'axis': 2  # Z axis
        },
        {
            'name': 'Y+ vers bloc',
            'start': (2.0, 8.0, 2.0),
            'end': (2.0, 12.0, 2.0),
            'expected_limit': 9.0,  # bloc_y - player_height = 10.0 - 1.0
            'axis': 1  # Y axis
        },
        {
            'name': 'Y- vers bloc',
            'start': (2.0, 12.0, 2.0),
            'end': (2.0, 8.0, 2.0),
            'expected_limit': 11.0,  # bloc_y + 1 = 10.0 + 1
            'axis': 1  # Y axis
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(symmetric_tests, 1):
        print(f"{i}. {test['name']}")
        
        safe_pos, collision_info = manager.resolve_collision(test['start'], test['end'])
        safe_coord = safe_pos[test['axis']]
        
        print(f"   Start: {test['start']}")
        print(f"   End:   {test['end']}")
        print(f"   Safe:  {safe_pos}")
        
        # Vérifier la limite selon la direction
        axis_names = ['X', 'Y', 'Z']
        axis_name = axis_names[test['axis']]
        
        tolerance = 0.001
        if abs(safe_coord - test['expected_limit']) > tolerance:
            print(f"   ❌ ÉCHEC: {axis_name}={safe_coord:.3f} != limite attendue {test['expected_limit']}")
            all_passed = False
        else:
            print(f"   ✅ SUCCÈS: {axis_name}={safe_coord:.3f} ≈ limite {test['expected_limit']}")
        
        print()
    
    return all_passed

def test_high_speed_movements():
    """Test que les mouvements à grande vitesse sont bloqués."""
    print("🔧 Test Mouvements à Grande Vitesse")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    high_speed_tests = [
        {
            'name': 'X+ très rapide',
            'start': (0.0, 5.0, 2.0),
            'end': (10.0, 5.0, 2.0),
            'max_x': 4.5
        },
        {
            'name': 'Z+ très rapide',
            'start': (2.0, 5.0, 0.0),
            'end': (2.0, 5.0, 10.0),
            'max_z': 4.5
        },
        {
            'name': 'Diagonal très rapide X+Z+',
            'start': (0.0, 5.0, 0.0),
            'end': (10.0, 5.0, 10.0),
            'max_x': 4.5,
            'max_z': 4.5
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(high_speed_tests, 1):
        print(f"{i}. {test['name']}")
        
        safe_pos, collision_info = manager.resolve_collision(test['start'], test['end'])
        
        print(f"   Start: {test['start']}")
        print(f"   End:   {test['end']}")
        print(f"   Safe:  {safe_pos}")
        
        # Vérifier les limites
        safe_x, safe_y, safe_z = safe_pos
        
        if 'max_x' in test and safe_x > test['max_x'] + 0.001:
            print(f"   ❌ ÉCHEC X: {safe_x:.3f} > limite {test['max_x']}")
            all_passed = False
        else:
            print(f"   ✅ X OK: {safe_x:.3f}")
        
        if 'max_z' in test and safe_z > test['max_z'] + 0.001:
            print(f"   ❌ ÉCHEC Z: {safe_z:.3f} > limite {test['max_z']}")
            all_passed = False
        else:
            print(f"   ✅ Z OK: {safe_z:.3f}")
        
        print()
    
    return all_passed

def main():
    """Test complet de la correction du bug X+ Z+."""
    print("🎯 TEST COMPLET DE CORRECTION DU BUG X+ Z+")
    print("=" * 60)
    print("Validation de la solution selon la spécification:")
    print("- Résolution stricte par axe (X, Y, Z)")
    print("- Snapping à la limite externe: bloc_x - largeur/2")
    print("- Logique parfaitement symétrique")
    print("- Blocage des mouvements haute vitesse")
    print()
    
    # Exécuter tous les tests
    test1 = test_x_plus_strict_blocking()
    test2 = test_z_plus_strict_blocking()
    test3 = test_symmetric_logic_all_axes()
    test4 = test_high_speed_movements()
    
    all_passed = test1 and test2 and test3 and test4
    
    print("=" * 60)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 60)
    
    if all_passed:
        print("🎉 CORRECTION RÉUSSIE!")
        print("✅ Blocage strict X+ implémenté")
        print("✅ Blocage strict Z+ implémenté")
        print("✅ Logique symétrique pour tous axes")
        print("✅ Mouvements haute vitesse bloqués")
        print()
        print("Le bug de collision X+ Z+ est entièrement corrigé!")
        return True
    else:
        print("🚨 CORRECTION INCOMPLÈTE")
        print("Certains tests échouent encore.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)