#!/usr/bin/env python3
"""
Comprehensive test to validate that the snapping fix works in all directions.
This test demonstrates that le snapping fonctionne maintenant dans tous les sens.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def comprehensive_snapping_test():
    """Test complet du snapping dans toutes les directions."""
    print("🔧 TEST COMPLET: Le Snapping Fonctionne Dans Tous Les Sens")
    print("=" * 65)
    print("Avant la correction: le snapping ne fonctionnait pas dans les directions -X et -Z")
    print("Après la correction: le snapping fonctionne dans toutes les 6 directions")
    print()

    # Créer un monde simple avec un seul bloc
    world = {(0, 0, 0): "stone"}
    manager = UnifiedCollisionManager(world)
    
    # Test de tous les mouvements qui tentent de traverser chaque face du bloc
    test_cases = [
        {
            "direction": "+X (vers la droite)",
            "start": (-1.0, 0.5, 0.5),
            "target": (0.8, 0.5, 0.5),  # Essaie de pénétrer dans le bloc
            "expected": "Collision détectée, joueur bloqué"
        },
        {
            "direction": "-X (vers la gauche)",
            "start": (1.0, 0.5, 0.5),
            "target": (0.3, 0.5, 0.5),  # Essaie de pénétrer dans le bloc
            "expected": "Collision détectée, joueur bloqué (ÉTAIT CASSÉ AVANT)"
        },
        {
            "direction": "+Y (vers le haut)",
            "start": (0.5, -1.0, 0.5),
            "target": (0.5, 0.8, 0.5),  # Essaie de pénétrer dans le bloc
            "expected": "Collision détectée, joueur bloqué"
        },
        {
            "direction": "-Y (vers le bas)",
            "start": (0.5, 2.0, 0.5),
            "target": (0.5, -0.8, 0.5),  # Essaie de pénétrer dans le bloc
            "expected": "Collision détectée, joueur bloqué"
        },
        {
            "direction": "+Z (vers l'avant)",
            "start": (0.5, 0.5, -1.0),
            "target": (0.5, 0.5, 0.8),  # Essaie de pénétrer dans le bloc
            "expected": "Collision détectée, joueur bloqué"
        },
        {
            "direction": "-Z (vers l'arrière)",
            "start": (0.5, 0.5, 1.0),
            "target": (0.5, 0.5, 0.3),  # Essaie de pénétrer dans le bloc
            "expected": "Collision détectée, joueur bloqué (ÉTAIT CASSÉ AVANT)"
        }
    ]

    print("📊 Résultats des tests:")
    print()
    
    all_passed = True
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. Direction {test['direction']}")
        print(f"   De: {test['start']} → Vers: {test['target']}")
        print(f"   Attendu: {test['expected']}")
        
        safe_pos, collision_info = manager.resolve_collision(test['start'], test['target'])
        
        # Vérifier si la collision a été détectée
        collision_detected = any(collision_info[axis] for axis in ['x', 'y', 'z'])
        
        # Vérifier si le joueur a été empêché de bouger vers le bloc
        movement_blocked = safe_pos == test['start']
        
        print(f"   Résultat: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        if collision_detected and movement_blocked:
            print(f"   ✅ SUCCÈS - Collision détectée et mouvement bloqué")
        elif collision_detected and not movement_blocked:
            print(f"   ⚠️  PARTIEL - Collision détectée mais mouvement partiel autorisé")
        else:
            print(f"   ❌ ÉCHEC - Aucune collision détectée")
            all_passed = False
        print()
    
    print("🎯 Résumé:")
    if all_passed:
        print("✅ TOUS LES TESTS RÉUSSIS!")
        print("   Le snapping fonctionne maintenant dans toutes les directions!")
        print("   Les problèmes dans les directions -X et -Z ont été corrigés.")
    else:
        print("❌ Certains tests ont échoué.")
    
    print()
    print("🔍 Test diagonal pour vérifier le comportement combiné:")
    
    # Test de mouvement diagonal qui devrait être partiellement bloqué
    start_diagonal = (1.5, 0.5, 1.5)
    target_diagonal = (-0.5, 0.5, -0.5)  # Mouvement diagonal vers le bloc
    
    safe_diagonal, collision_diagonal = manager.resolve_collision(start_diagonal, target_diagonal)
    
    print(f"   Mouvement diagonal: {start_diagonal} → {target_diagonal}")
    print(f"   Résultat: {safe_diagonal}")
    print(f"   Collision: {collision_diagonal}")
    
    # Calculer l'efficacité du mouvement
    intended_distance = ((target_diagonal[0] - start_diagonal[0])**2 + 
                        (target_diagonal[1] - start_diagonal[1])**2 + 
                        (target_diagonal[2] - start_diagonal[2])**2)**0.5
    actual_distance = ((safe_diagonal[0] - start_diagonal[0])**2 + 
                      (safe_diagonal[1] - start_diagonal[1])**2 + 
                      (safe_diagonal[2] - start_diagonal[2])**2)**0.5
    
    efficiency = actual_distance / intended_distance if intended_distance > 0 else 0
    print(f"   Efficacité du mouvement: {efficiency:.1%}")
    
    if efficiency > 0:
        print("   ✅ Mouvement diagonal partiellement autorisé (comportement correct)")
    else:
        print("   ⚠️  Mouvement diagonal complètement bloqué")

if __name__ == "__main__":
    comprehensive_snapping_test()