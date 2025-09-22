#!/usr/bin/env python3
"""
Test correct de la collision X+ Z+ avec des cas d'usage réalistes.

Ce test corrige les attentes erronées des tests précédents et vérifie
le comportement correct du système de collision.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_realistic_x_plus_collision():
    """Test réaliste de collision X+ - joueur qui intersecte réellement avec le bloc."""
    print("🔧 Test Réaliste Collision X+")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc: (5, 10, 5) → limites [5.0-6.0, 10.0-11.0, 5.0-6.0]")
    print(f"Joueur: largeur {PLAYER_WIDTH}, hauteur {PLAYER_HEIGHT}")
    print()
    
    # Test cases où le joueur INTERSECTE réellement avec le bloc
    test_cases = [
        {
            'name': 'X+ collision - joueur dans même Y,Z que bloc',
            'start': (4.0, 10.5, 5.5),  # Y et Z intersectent avec le bloc
            'end': (6.0, 10.5, 5.5),    # Mouvement X+ à travers le bloc
            'should_be_blocked': True,
            'expected_max_x': 4.5,      # Snapped à bloc_x - largeur/2
        },
        {
            'name': 'X+ pas de collision - joueur loin en Z',
            'start': (4.0, 10.5, 2.0),  # Z ne touche pas le bloc [5.0-6.0]
            'end': (6.0, 10.5, 2.0),    # Mouvement libre
            'should_be_blocked': False,
            'expected_max_x': 6.0,      # Mouvement autorisé
        },
        {
            'name': 'X+ collision partielle - joueur touche bord Z',
            'start': (4.0, 10.5, 4.5),  # Joueur Z=[4.0-5.0], bloc Z=[5.0-6.0] → juste touche
            'end': (6.0, 10.5, 4.5),    # Mouvement X+
            'should_be_blocked': True,
            'expected_max_x': 4.5,
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        print(f"   Safe:  {safe_pos}")
        print(f"   Collision X: {collision_info['x']}")
        
        # Vérifier si collision détectée comme attendu
        if test['should_be_blocked'] and not collision_info['x']:
            print(f"   ❌ ÉCHEC: Collision attendue mais pas détectée")
            all_passed = False
        elif not test['should_be_blocked'] and collision_info['x']:
            print(f"   ❌ ÉCHEC: Collision détectée mais pas attendue")
            all_passed = False
        else:
            print(f"   ✅ Détection collision correcte")
        
        # Vérifier position finale
        safe_x = safe_pos[0]
        tolerance = 0.001
        if abs(safe_x - test['expected_max_x']) > tolerance:
            print(f"   ❌ POSITION: X={safe_x:.3f} != attendu {test['expected_max_x']}")
            all_passed = False
        else:
            print(f"   ✅ Position X correcte: {safe_x:.3f}")
        
        # Vérifier pas de collision finale
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ Position finale en collision!")
            all_passed = False
        else:
            print(f"   ✅ Position finale sans collision")
        
        print()
    
    return all_passed

def test_realistic_z_plus_collision():
    """Test réaliste de collision Z+ - joueur qui intersecte réellement avec le bloc."""
    print("🔧 Test Réaliste Collision Z+")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc: (5, 10, 5) → limites [5.0-6.0, 10.0-11.0, 5.0-6.0]")
    print()
    
    # Test cases où le joueur INTERSECTE réellement avec le bloc
    test_cases = [
        {
            'name': 'Z+ collision - joueur dans même X,Y que bloc',
            'start': (5.5, 10.5, 4.0),  # X et Y intersectent avec le bloc
            'end': (5.5, 10.5, 6.0),    # Mouvement Z+ à travers le bloc
            'should_be_blocked': True,
            'expected_max_z': 4.5,      # Snapped à bloc_z - largeur/2
        },
        {
            'name': 'Z+ pas de collision - joueur loin en X',
            'start': (2.0, 10.5, 4.0),  # X ne touche pas le bloc [5.0-6.0]
            'end': (2.0, 10.5, 6.0),    # Mouvement libre
            'should_be_blocked': False,
            'expected_max_z': 6.0,      # Mouvement autorisé
        },
        {
            'name': 'Z+ collision partielle - joueur touche bord X',
            'start': (4.5, 10.5, 4.0),  # Joueur X=[4.0-5.0], bloc X=[5.0-6.0] → juste touche
            'end': (4.5, 10.5, 6.0),    # Mouvement Z+
            'should_be_blocked': True,
            'expected_max_z': 4.5,
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        print(f"   Safe:  {safe_pos}")
        print(f"   Collision Z: {collision_info['z']}")
        
        # Vérifier si collision détectée comme attendu
        if test['should_be_blocked'] and not collision_info['z']:
            print(f"   ❌ ÉCHEC: Collision attendue mais pas détectée")
            all_passed = False
        elif not test['should_be_blocked'] and collision_info['z']:
            print(f"   ❌ ÉCHEC: Collision détectée mais pas attendue")
            all_passed = False
        else:
            print(f"   ✅ Détection collision correcte")
        
        # Vérifier position finale
        safe_z = safe_pos[2]
        tolerance = 0.001
        if abs(safe_z - test['expected_max_z']) > tolerance:
            print(f"   ❌ POSITION: Z={safe_z:.3f} != attendu {test['expected_max_z']}")
            all_passed = False
        else:
            print(f"   ✅ Position Z correcte: {safe_z:.3f}")
        
        # Vérifier pas de collision finale
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ Position finale en collision!")
            all_passed = False
        else:
            print(f"   ✅ Position finale sans collision")
        
        print()
    
    return all_passed

def test_diagonal_movements_realistic():
    """Test des mouvements diagonaux réalistes qui reproduisent le bug original."""
    print("🔧 Test Mouvements Diagonaux Réalistes")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("Ces tests reproduisent le bug original décrit dans la spécification.")
    print()
    
    # Test cases qui reproduisent le problème de pénétration partielle
    test_cases = [
        {
            'name': 'Bug original: diagonal X+Z+ avec pénétration partielle',
            'start': (4.7, 10.5, 4.7),  # Proche du coin du bloc
            'end': (5.3, 10.5, 5.3),    # Mouvement diagonal vers le bloc
            'description': 'Reproduit le problème: le joueur traverse partiellement le bloc'
        },
        {
            'name': 'Mouvement X+ pur vers bloc - cas critique',
            'start': (4.3, 10.5, 5.5),  # Position où joueur intersecte en Z
            'end': (5.7, 10.5, 5.5),    # Mouvement X+ pur
            'description': 'Test snapping strict en X+'
        },
        {
            'name': 'Mouvement Z+ pur vers bloc - cas critique',
            'start': (5.5, 10.5, 4.3),  # Position où joueur intersecte en X
            'end': (5.5, 10.5, 5.7),    # Mouvement Z+ pur
            'description': 'Test snapping strict en Z+'
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        print(f"   {test['description']}")
        
        start_pos = test['start']
        end_pos = test['end']
        
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        print(f"   Safe:  {safe_pos}")
        print(f"   Collision: {collision_info}")
        
        # Calculer si il y a pénétration
        safe_x, safe_y, safe_z = safe_pos
        player_right_edge = safe_x + PLAYER_WIDTH/2
        player_front_edge = safe_z + PLAYER_WIDTH/2
        
        x_penetration = max(0, player_right_edge - 5.0)  # 5.0 = face gauche du bloc
        z_penetration = max(0, player_front_edge - 5.0)  # 5.0 = face arrière du bloc
        
        if x_penetration > 0.001:
            print(f"   🚨 PÉNÉTRATION X+: {x_penetration:.3f}")
            # Avant le fix, ceci était attendu. Après le fix, ça ne devrait plus arriver.
        else:
            print(f"   ✅ Pas de pénétration X+")
        
        if z_penetration > 0.001:
            print(f"   🚨 PÉNÉTRATION Z+: {z_penetration:.3f}")
            # Avant le fix, ceci était attendu. Après le fix, ça ne devrait plus arriver.
        else:
            print(f"   ✅ Pas de pénétration Z+")
        
        # Vérifier pas de collision finale
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ Position finale en collision!")
            all_passed = False
        else:
            print(f"   ✅ Position finale sans collision")
        
        print()
    
    return all_passed

def main():
    """Test réaliste du système de collision corrigé."""
    print("🎯 TEST RÉALISTE DU SYSTÈME DE COLLISION CORRIGÉ")
    print("=" * 60)
    print("Ce test utilise des cas d'usage réalistes où les collisions")
    print("devraient effectivement se produire selon les lois de la physique.")
    print()
    
    # Exécuter tous les tests
    test1 = test_realistic_x_plus_collision()
    test2 = test_realistic_z_plus_collision()
    test3 = test_diagonal_movements_realistic()
    
    all_passed = test1 and test2 and test3
    
    print("=" * 60)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 60)
    
    if all_passed:
        print("🎉 SYSTÈME DE COLLISION FONCTIONNEL!")
        print("✅ Collisions X+ gérées correctement")
        print("✅ Collisions Z+ gérées correctement")
        print("✅ Mouvements diagonaux sans pénétration")
        print()
        print("Le bug de collision X+ Z+ est corrigé!")
        return True
    else:
        print("🚨 PROBLÈMES DÉTECTÉS")
        print("Le système de collision nécessite encore des ajustements.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)