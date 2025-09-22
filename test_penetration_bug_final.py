#!/usr/bin/env python3
"""
Test final pour reproduire exactement le bug décrit dans la spécification:
"Le joueur traverse partiellement les blocs lorsqu'il se déplace sur l'axe x+ ou z+, 
le blocage n'est pas immédiat"

Ce test créé des scénarios où le système permet une pénétration partielle.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_partial_penetration_x_plus():
    """Test pour démontrer la pénétration partielle en X+."""
    print("🚨 Test Pénétration Partielle X+")
    print("=" * 50)
    
    # Créer un scénario où le joueur peut pénétrer partiellement
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("Configuration:")
    print(f"  Bloc: (5, 10, 5) → limites X [5.0 - 6.0]")
    print(f"  Joueur: largeur {PLAYER_WIDTH} → centre ±{PLAYER_WIDTH/2}")
    print(f"  Limite théorique: joueur ne doit pas dépasser X = 4.5")
    print()
    
    # Tester le comportement avec axis-by-axis movement
    test_movements = [
        {
            'name': 'Mouvement diagonal X+Z+ avec collision uniquement en Z',
            'start': (4.8, 10.5, 4.3),   # Près de la limite X, libre en Z
            'end': (5.2, 10.5, 5.7),     # Destination dans le bloc
        },
        {
            'name': 'Mouvement X+ pur vers bloc',
            'start': (4.3, 10.5, 5.5),   # Libre, centré sur Z du bloc
            'end': (5.3, 10.5, 5.5),     # Destination dans le bloc
        },
        {
            'name': 'Petit mouvement X+ proche limite',
            'start': (4.45, 10.5, 5.5),  # Très proche limite
            'end': (4.55, 10.5, 5.5),    # Franchit la limite
        }
    ]
    
    issues_found = []
    
    for i, test in enumerate(test_movements, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        
        # Résoudre le mouvement
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        print(f"   Safe:  {safe_pos}")
        print(f"   Collision: {collision_info}")
        
        # Analyser la position finale
        final_x = safe_pos[0]
        final_z = safe_pos[2]
        
        # Calculer la position du bord droit du joueur
        player_right_edge = final_x + PLAYER_WIDTH/2
        
        # La limite stricte est à X = 5.0 (face du bloc)
        if player_right_edge > 5.0:
            penetration = player_right_edge - 5.0
            print(f"   🚨 PÉNÉTRATION X+ DÉTECTÉE: {penetration:.3f} blocs!")
            print(f"      Joueur centre X={final_x:.3f}, bord droit X={player_right_edge:.3f}")
            print(f"      Limite bloc X=5.0 → pénétration de {penetration:.3f}")
            issues_found.append(f"Test {i}: Pénétration X+ de {penetration:.3f}")
        
        # Vérifier que la position finale n'a pas de collision
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ POSITION FINALE EN COLLISION!")
            issues_found.append(f"Test {i}: Position finale en collision")
        
        print()
    
    return len(issues_found) == 0, issues_found

def test_partial_penetration_z_plus():
    """Test pour démontrer la pénétration partielle en Z+."""
    print("🚨 Test Pénétration Partielle Z+")
    print("=" * 50)
    
    # Créer un scénario où le joueur peut pénétrer partiellement
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("Configuration:")
    print(f"  Bloc: (5, 10, 5) → limites Z [5.0 - 6.0]")
    print(f"  Joueur: largeur {PLAYER_WIDTH} → centre ±{PLAYER_WIDTH/2}")
    print(f"  Limite théorique: joueur ne doit pas dépasser Z = 4.5")
    print()
    
    # Tester le comportement avec axis-by-axis movement
    test_movements = [
        {
            'name': 'Mouvement diagonal X+Z+ avec collision uniquement en X',
            'start': (4.3, 10.5, 4.8),   # Libre en X, près de la limite Z
            'end': (5.7, 10.5, 5.2),     # Destination dans le bloc
        },
        {
            'name': 'Mouvement Z+ pur vers bloc',
            'start': (5.5, 10.5, 4.3),   # Centré sur X du bloc, libre
            'end': (5.5, 10.5, 5.3),     # Destination dans le bloc
        },
        {
            'name': 'Petit mouvement Z+ proche limite',
            'start': (5.5, 10.5, 4.45),  # Très proche limite
            'end': (5.5, 10.5, 4.55),    # Franchit la limite
        }
    ]
    
    issues_found = []
    
    for i, test in enumerate(test_movements, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        
        # Résoudre le mouvement
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        print(f"   Safe:  {safe_pos}")
        print(f"   Collision: {collision_info}")
        
        # Analyser la position finale
        final_x = safe_pos[0]
        final_z = safe_pos[2]
        
        # Calculer la position du bord avant du joueur
        player_front_edge = final_z + PLAYER_WIDTH/2
        
        # La limite stricte est à Z = 5.0 (face du bloc)
        if player_front_edge > 5.0:
            penetration = player_front_edge - 5.0
            print(f"   🚨 PÉNÉTRATION Z+ DÉTECTÉE: {penetration:.3f} blocs!")
            print(f"      Joueur centre Z={final_z:.3f}, bord avant Z={player_front_edge:.3f}")
            print(f"      Limite bloc Z=5.0 → pénétration de {penetration:.3f}")
            issues_found.append(f"Test {i}: Pénétration Z+ de {penetration:.3f}")
        
        # Vérifier que la position finale n'a pas de collision
        final_collision = manager.check_block_collision(safe_pos)
        if final_collision:
            print(f"   ❌ POSITION FINALE EN COLLISION!")
            issues_found.append(f"Test {i}: Position finale en collision")
        
        print()
    
    return len(issues_found) == 0, issues_found

def test_high_speed_movements():
    """Test que les mouvements à grande vitesse sont également correctement bloqués."""
    print("⚡ Test Mouvements à Grande Vitesse")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    high_speed_tests = [
        {
            'name': 'Mouvement X+ très rapide',
            'start': (2.0, 10.5, 5.5),
            'end': (8.0, 10.5, 5.5),
        },
        {
            'name': 'Mouvement Z+ très rapide',
            'start': (5.5, 10.5, 2.0),
            'end': (5.5, 10.5, 8.0),
        },
        {
            'name': 'Mouvement diagonal très rapide',
            'start': (2.0, 10.5, 2.0),
            'end': (8.0, 10.5, 8.0),
        }
    ]
    
    issues_found = []
    
    for i, test in enumerate(high_speed_tests, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        print(f"   Safe:  {safe_pos}")
        
        # Vérifier qu'aucune pénétration n'a lieu
        player_right_edge = safe_pos[0] + PLAYER_WIDTH/2
        player_front_edge = safe_pos[2] + PLAYER_WIDTH/2
        
        x_penetration = max(0, player_right_edge - 5.0)
        z_penetration = max(0, player_front_edge - 5.0)
        
        if x_penetration > 0:
            print(f"   🚨 PÉNÉTRATION X+ à haute vitesse: {x_penetration:.3f}")
            issues_found.append(f"Test {i}: Pénétration X+ haute vitesse {x_penetration:.3f}")
        
        if z_penetration > 0:
            print(f"   🚨 PÉNÉTRATION Z+ à haute vitesse: {z_penetration:.3f}")
            issues_found.append(f"Test {i}: Pénétration Z+ haute vitesse {z_penetration:.3f}")
        
        print()
    
    return len(issues_found) == 0, issues_found

def main():
    """Fonction principale pour tester les pénétrations partielles."""
    print("🔍 Test de Reproduction du Bug de Pénétration Partielle")
    print("Objectif: Démontrer que le système actuel permet la traversée partielle")
    print()
    
    try:
        # Test X+ penetration
        success1, issues_x = test_partial_penetration_x_plus()
        
        # Test Z+ penetration  
        success2, issues_z = test_partial_penetration_z_plus()
        
        # Test high speed movements
        success3, issues_speed = test_high_speed_movements()
        
        overall_success = success1 and success2 and success3
        
        print("=" * 60)
        print("📊 RÉSUMÉ FINAL")
        print("=" * 60)
        
        if overall_success:
            print("✅ AUCUNE PÉNÉTRATION PARTIELLE DÉTECTÉE")
            print("Le système de collision fonctionne correctement")
        else:
            print("❌ PÉNÉTRATIONS PARTIELLES CONFIRMÉES")
            print("Le bug décrit dans la spécification est reproduit:")
            
            if not success1:
                print("\n🚨 Problèmes X+:")
                for issue in issues_x:
                    print(f"  • {issue}")
            
            if not success2:
                print("\n🚨 Problèmes Z+:")
                for issue in issues_z:
                    print(f"  • {issue}")
            
            if not success3:
                print("\n🚨 Problèmes haute vitesse:")
                for issue in issues_speed:
                    print(f"  • {issue}")
            
            print("\n🔧 SOLUTION REQUISE:")
            print("Implémenter la résolution stricte par axe avec snapping précis")
            print("comme décrit dans la spécification du problème.")
        
        return overall_success
        
    except Exception as e:
        print(f"💥 Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)