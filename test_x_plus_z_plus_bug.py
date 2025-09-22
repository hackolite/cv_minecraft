#!/usr/bin/env python3
"""
Test spécifique pour reproduire le bug décrit:
"Le joueur traverse partiellement les blocs lorsqu'il se déplace sur l'axe x+ ou z+, 
le blocage n'est pas immédiat"

Ce test va tenter de reproduire exactement ce comportement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_single_axis_x_plus_movement():
    """Test movement strictement sur l'axe X+ pour reproduire le bug."""
    print("🔍 Test Mouvement X+ Strict")
    print("=" * 50)
    
    # Créer un monde avec un bloc simple
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc à la position: (5, 10, 5)")
    print(f"Dimensions du joueur: {PLAYER_WIDTH}×{PLAYER_HEIGHT}")
    print()
    
    # Test avec position Y centrée au niveau du bloc
    # Joueur de largeur 1.0, donc ±0.5 autour du centre
    test_cases = [
        {
            'name': 'Mouvement X+ petit pas',
            'start': (4.3, 10.5, 5.5),  # Y centré sur le bloc, Z au centre du bloc
            'end': (5.3, 10.5, 5.5),    # Mouvement X+ qui devrait entrer dans le bloc
            'expected_blocked': True
        },
        {
            'name': 'Mouvement X+ grand pas',  
            'start': (4.0, 10.5, 5.5),  # Y centré sur le bloc, Z au centre du bloc
            'end': (6.0, 10.5, 5.5),    # Mouvement X+ qui devrait être bloqué immédiatement
            'expected_blocked': True
        },
        {
            'name': 'Mouvement X+ proche limite',
            'start': (4.49, 10.5, 5.5), # Très proche de la limite du bloc
            'end': (4.51, 10.5, 5.5),   # Petit pas qui traverse la limite
            'expected_blocked': True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        start_pos = test_case['start']
        end_pos = test_case['end']
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        
        # Vérifier les collisions
        start_collision = manager.check_block_collision(start_pos)
        end_collision = manager.check_block_collision(end_pos)
        
        print(f"   Start collision: {start_collision}")
        print(f"   End collision: {end_collision}")
        
        # Résoudre le mouvement
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Analyser le résultat
        movement_delta_x = abs(safe_pos[0] - start_pos[0])
        intended_delta_x = abs(end_pos[0] - start_pos[0])
        
        print(f"   Movement delta X: {movement_delta_x:.3f} (intended: {intended_delta_x:.3f})")
        
        # Détecter si il y a pénétration partielle
        if movement_delta_x > 0 and movement_delta_x < intended_delta_x:
            if safe_pos[0] > 4.5:  # La limite du bloc est à x=5, et le joueur fait ±0.5
                print(f"   ⚠️  PÉNÉTRATION PARTIELLE DÉTECTÉE!")
                print(f"       Le joueur a bougé de {movement_delta_x:.3f} au lieu d'être bloqué immédiatement")
                print(f"       Position finale X={safe_pos[0]:.3f} > limite bloc (4.5)")
                return False
        
        # Vérifier si le mouvement est correctement bloqué
        if end_collision and not collision_info['x']:
            print(f"   ❌ BUG: La destination a une collision mais l'axe X n'est pas marqué comme bloqué!")
            return False
        
        print()
    
    return True

def test_single_axis_z_plus_movement():
    """Test movement strictement sur l'axe Z+ pour reproduire le bug."""
    print("🔍 Test Mouvement Z+ Strict")
    print("=" * 50)
    
    # Créer un monde avec un bloc simple
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc à la position: (5, 10, 5)")
    print(f"Dimensions du joueur: {PLAYER_WIDTH}×{PLAYER_HEIGHT}")
    print()
    
    # Test avec position Y centrée au niveau du bloc
    test_cases = [
        {
            'name': 'Mouvement Z+ petit pas',
            'start': (5.5, 10.5, 4.3),  # X au centre du bloc, Y centré sur le bloc
            'end': (5.5, 10.5, 5.3),    # Mouvement Z+ qui devrait entrer dans le bloc
            'expected_blocked': True
        },
        {
            'name': 'Mouvement Z+ grand pas',  
            'start': (5.5, 10.5, 4.0),  # X au centre du bloc, Y centré sur le bloc
            'end': (5.5, 10.5, 6.0),    # Mouvement Z+ qui devrait être bloqué immédiatement
            'expected_blocked': True
        },
        {
            'name': 'Mouvement Z+ proche limite',
            'start': (5.5, 10.5, 4.49), # Très proche de la limite du bloc
            'end': (5.5, 10.5, 4.51),   # Petit pas qui traverse la limite
            'expected_blocked': True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        start_pos = test_case['start']
        end_pos = test_case['end']
        
        print(f"   Start: {start_pos}")
        print(f"   End:   {end_pos}")
        
        # Vérifier les collisions
        start_collision = manager.check_block_collision(start_pos)
        end_collision = manager.check_block_collision(end_pos)
        
        print(f"   Start collision: {start_collision}")
        print(f"   End collision: {end_collision}")
        
        # Résoudre le mouvement
        safe_pos, collision_info = manager.resolve_collision(start_pos, end_pos)
        
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Analyser le résultat
        movement_delta_z = abs(safe_pos[2] - start_pos[2])
        intended_delta_z = abs(end_pos[2] - start_pos[2])
        
        print(f"   Movement delta Z: {movement_delta_z:.3f} (intended: {intended_delta_z:.3f})")
        
        # Détecter si il y a pénétration partielle
        if movement_delta_z > 0 and movement_delta_z < intended_delta_z:
            if safe_pos[2] > 4.5:  # La limite du bloc est à z=5, et le joueur fait ±0.5
                print(f"   ⚠️  PÉNÉTRATION PARTIELLE DÉTECTÉE!")
                print(f"       Le joueur a bougé de {movement_delta_z:.3f} au lieu d'être bloqué immédiatement")
                print(f"       Position finale Z={safe_pos[2]:.3f} > limite bloc (4.5)")
                return False
        
        # Vérifier si le mouvement est correctement bloqué
        if end_collision and not collision_info['z']:
            print(f"   ❌ BUG: La destination a une collision mais l'axe Z n'est pas marqué comme bloqué!")
            return False
        
        print()
    
    return True

def test_precise_collision_boundaries():
    """Test précis des limites de collision pour détecter les erreurs de boundary."""
    print("🎯 Test Précis des Limites de Collision")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("Bloc: (5, 10, 5) → limites X: [5.0, 6.0], Z: [5.0, 6.0]")
    print("Joueur: largeur 1.0 → position ±0.5")
    print("Limite de collision: joueur centre à X=4.5 ou Z=4.5")
    print()
    
    # Test positions critiques
    critical_positions = [
        ("Juste avant limite X", (4.49, 10.5, 5.5)),
        ("Exactement à limite X", (4.5, 10.5, 5.5)),
        ("Juste après limite X", (4.51, 10.5, 5.5)),
        ("Juste avant limite Z", (5.5, 10.5, 4.49)),
        ("Exactement à limite Z", (5.5, 10.5, 4.5)),
        ("Juste après limite Z", (5.5, 10.5, 4.51)),
    ]
    
    for name, pos in critical_positions:
        collision = manager.check_block_collision(pos)
        print(f"{name}: {pos} → collision: {collision}")
        
        # Les positions "juste après limite" devraient avoir une collision
        if "après limite" in name and not collision:
            print(f"   ❌ ERREUR: Position dans le bloc mais pas de collision détectée!")
            return False
        # Les positions "juste avant limite" ne devraient pas avoir de collision  
        elif "avant limite" in name and collision:
            print(f"   ❌ ERREUR: Position hors du bloc mais collision détectée!")
            return False
    
    print()
    return True

def main():
    """Fonction principale pour tester le bug X+ et Z+."""
    print("🐛 Test Bug de Collision X+ et Z+")
    print("Problem: Le joueur traverse partiellement les blocs lors du déplacement en x+ ou z+")
    print()
    
    try:
        # Test des limites précises
        success1 = test_precise_collision_boundaries()
        
        # Test mouvement X+
        success2 = test_single_axis_x_plus_movement()
        
        # Test mouvement Z+
        success3 = test_single_axis_z_plus_movement()
        
        overall_success = success1 and success2 and success3
        
        print("=" * 60)
        if overall_success:
            print("✅ AUCUN BUG DÉTECTÉ")
            print("Le système de collision fonctionne correctement pour X+ et Z+")
        else:
            print("❌ BUG CONFIRMÉ")
            print("Le système de collision permet la pénétration partielle en X+ ou Z+")
            
        return overall_success
        
    except Exception as e:
        print(f"💥 Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)