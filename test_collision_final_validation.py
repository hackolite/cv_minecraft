#!/usr/bin/env python3
"""
Test pour valider que la fix fonctionne correctement
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_fixed_collision_system():
    """Test final pour valider que le système de collision est corrigé."""
    print("✅ Test de Validation du Système de Collision Corrigé")
    print("=" * 60)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc: (5, 10, 5) → limites [5.0-6.0, 10.0-11.0, 5.0-6.0]")
    print(f"Joueur: largeur {PLAYER_WIDTH}, hauteur {PLAYER_HEIGHT}")
    print(f"Limite théorique: X <= 4.5, Z <= 4.5")
    print()
    
    # Test cases qui devraient maintenant fonctionner
    test_cases = [
        {
            'name': 'X+ pur vers bloc - devrait être bloqué',
            'start': (4.3, 10.5, 5.5),
            'end': (5.3, 10.5, 5.5),
            'max_allowed_x': 4.5,
            'max_allowed_z': 6.0  # Z is not constrained in this test
        },
        {
            'name': 'Z+ pur vers bloc - devrait être bloqué',
            'start': (5.5, 10.5, 4.3),
            'end': (5.5, 10.5, 5.3),
            'max_allowed_x': 6.0,  # X is not constrained in this test
            'max_allowed_z': 4.5
        },
        {
            'name': 'Mouvement sûr loin du bloc',
            'start': (3.0, 10.5, 3.0),
            'end': (4.0, 10.5, 4.0),
            'max_allowed_x': 10.0,  # Should be unrestricted
            'max_allowed_z': 10.0
        },
        {
            'name': 'Mouvement vers limite exacte',
            'start': (4.0, 10.5, 5.5),
            'end': (4.5, 10.5, 5.5),
            'max_allowed_x': 4.5,
            'max_allowed_z': 6.0
        }
    ]
    
    all_tests_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        print(f"   Safe:  {safe_pos}")
        print(f"   Collision: {collision_info}")
        
        # Vérifier les limites
        final_x, final_y, final_z = safe_pos
        player_right_edge = final_x + PLAYER_WIDTH/2
        player_front_edge = final_z + PLAYER_WIDTH/2
        
        # Vérifier la limite X
        if player_right_edge > test['max_allowed_x']:
            penetration_x = player_right_edge - test['max_allowed_x']
            print(f"   ❌ PÉNÉTRATION X: {penetration_x:.3f} (limite: {test['max_allowed_x']})")
            all_tests_passed = False
        else:
            print(f"   ✅ X OK: bord à {player_right_edge:.3f} <= {test['max_allowed_x']}")
        
        # Vérifier la limite Z
        if player_front_edge > test['max_allowed_z']:
            penetration_z = player_front_edge - test['max_allowed_z']
            print(f"   ❌ PÉNÉTRATION Z: {penetration_z:.3f} (limite: {test['max_allowed_z']})")
            all_tests_passed = False
        else:
            print(f"   ✅ Z OK: bord à {player_front_edge:.3f} <= {test['max_allowed_z']}")
        
        # Vérifier qu'il n'y a pas de collision à la position finale
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ COLLISION FINALE DÉTECTÉE!")
            all_tests_passed = False
        else:
            print(f"   ✅ Position finale sans collision")
        
        print()
    
    return all_tests_passed

def main():
    success = test_fixed_collision_system()
    
    print("=" * 60)
    if success:
        print("🎉 SYSTÈME DE COLLISION CORRIGÉ!")
        print("Tous les tests passent, le bug de pénétration partielle est résolu.")
        return True
    else:
        print("🚨 DES PROBLÈMES SUBSISTENT")
        print("Le système de collision nécessite encore des ajustements.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)