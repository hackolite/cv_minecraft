#!/usr/bin/env python3
"""
Test pour reproduire le problème spécifique mentionné:
"quand ma position fait x+ et z+ et collisionne, je rentre dans le bloc"
"affiche dans la windows collision detectée quand il y a collision"
"la collision est souvent detectée mais sous certaines faces je rentre dans le bloc"

Ce test va créer des scénarios où la collision est détectée mais le joueur 
peut encore entrer dans le bloc sous certaines conditions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT
import logging

# Configure logging to see collision messages
logging.basicConfig(level=logging.DEBUG)
collision_logger = logging.getLogger('collision')

def print_collision_debug(message):
    """Affiche les messages de collision dans la fenêtre."""
    print(f"🪟 COLLISION DETECTÉE: {message}")

def test_face_specific_collision_issues():
    """Test les problèmes de collision spécifiques à certaines faces."""
    print("🔍 Test des problèmes de collision par face")
    print("=" * 60)
    
    # Créer un monde avec un seul bloc
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Bloc de pierre à: (5, 10, 5)")
    print(f"Dimensions du joueur: {PLAYER_WIDTH}×{PLAYER_HEIGHT}")
    print()
    
    # Test cases problématiques spécifiques
    test_cases = [
        {
            'name': 'Mouvement +X +Z - Position initiale près du coin',
            'start': (4.9, 10.5, 4.9),  # Très proche du coin du bloc
            'target': (5.1, 10.5, 5.1), # Petit mouvement vers l'intérieur
            'description': 'Mouvement diagonal vers le coin du bloc'
        },
        {
            'name': 'Mouvement +X +Z - Position limite',
            'start': (4.5, 10.5, 4.5),  # À la limite de la hitbox
            'target': (5.5, 10.5, 5.5), # Traverse complètement le bloc
            'description': 'Mouvement depuis le bord de la hitbox'
        },
        {
            'name': 'Mouvement +X +Z - Micro-mouvement',
            'start': (4.95, 10.5, 4.95), # Presque dans le bloc
            'target': (5.05, 10.5, 5.05), # Petit saut dans le bloc
            'description': 'Micro-mouvement qui pourrait bypass la détection'
        },
        {
            'name': 'Face Sud-Est (+X +Z)',
            'start': (4.8, 10.5, 4.8),   # Approche par le coin Sud-Est
            'target': (5.2, 10.5, 5.2),  # Entre dans le bloc
            'description': 'Entrée par la face Sud-Est du bloc'
        },
        {
            'name': 'Entrée par arête',
            'start': (4.99, 10.5, 5.0),  # Sur l\'arête X
            'target': (5.01, 10.5, 5.0), # Petit mouvement X
            'description': 'Mouvement le long d\'une arête'
        }
    ]
    
    collision_detected_count = 0
    penetration_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        print(f"   Description: {test['description']}")
        print(f"   Départ: {test['start']}")
        print(f"   Cible: {test['target']}")
        
        start_pos = test['start']
        target_pos = test['target']
        
        # Vérifier collision à la position de départ
        start_collision = manager.check_block_collision(start_pos)
        print(f"   Collision départ: {start_collision}")
        
        # Vérifier collision à la position cible
        target_collision = manager.check_block_collision(target_pos)
        print(f"   Collision cible: {target_collision}")
        
        if target_collision:
            collision_detected_count += 1
            print_collision_debug(f"Position cible {target_pos} en collision avec bloc")
        
        # Résoudre le mouvement
        safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        print(f"   Position sûre: {safe_pos}")
        print(f"   Info collision: {collision_info}")
        
        # Vérifier si la position "sûre" est réellement dans le bloc
        safe_collision = manager.check_block_collision(safe_pos)
        print(f"   Position sûre en collision: {safe_collision}")
        
        if safe_collision:
            penetration_count += 1
            print(f"   ❌ PROBLÈME: Position 'sûre' est dans le bloc!")
            print_collision_debug(f"Pénétration détectée à {safe_pos}")
        
        # Vérifier la distance parcourue
        distance_intended = ((target_pos[0] - start_pos[0])**2 + 
                           (target_pos[2] - start_pos[2])**2)**0.5
        distance_actual = ((safe_pos[0] - start_pos[0])**2 + 
                         (safe_pos[2] - start_pos[2])**2)**0.5
        
        print(f"   Distance prévue: {distance_intended:.3f}")
        print(f"   Distance réelle: {distance_actual:.3f}")
        
        # Si la distance réelle est proche de la distance prévue et qu'il y a collision,
        # c'est suspect
        if distance_actual > distance_intended * 0.8 and target_collision:
            print(f"   ⚠️  Mouvement suspect: grande distance malgré collision détectée")
        
        print()
    
    print("📊 RÉSUMÉ:")
    print(f"Total des tests: {len(test_cases)}")
    print(f"Collisions détectées: {collision_detected_count}")
    print(f"Pénétrations dans le bloc: {penetration_count}")
    
    if penetration_count > 0:
        print(f"❌ {penetration_count} cas de pénétration détectés!")
        return False
    else:
        print("✅ Aucune pénétration détectée")
        return True

def test_systematic_collision_detection():
    """Test systématique de la détection de collision autour du bloc."""
    print("\n🔬 Test systématique de détection de collision")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Grille de test autour du bloc
    test_positions = []
    for x_offset in [-0.6, -0.5, -0.4, -0.1, 0.0, 0.1, 0.4, 0.5, 0.6]:
        for z_offset in [-0.6, -0.5, -0.4, -0.1, 0.0, 0.1, 0.4, 0.5, 0.6]:
            pos = (5.0 + x_offset, 10.5, 5.0 + z_offset)
            test_positions.append(pos)
    
    collision_positions = []
    no_collision_positions = []
    
    for pos in test_positions:
        collision = manager.check_block_collision(pos)
        if collision:
            collision_positions.append(pos)
            print_collision_debug(f"Position {pos}")
        else:
            no_collision_positions.append(pos)
    
    print(f"Positions testées: {len(test_positions)}")
    print(f"Collisions détectées: {len(collision_positions)}")
    print(f"Pas de collision: {len(no_collision_positions)}")
    
    # Vérifier la cohérence: les positions très proches du centre du bloc 
    # devraient toutes être en collision
    center_pos = (5.0, 10.5, 5.0)
    center_collision = manager.check_block_collision(center_pos)
    print(f"Collision au centre du bloc {center_pos}: {center_collision}")
    
    if not center_collision:
        print("❌ PROBLÈME: Pas de collision au centre du bloc!")
        return False
    
    return True

def main():
    """Exécute tous les tests de collision."""
    print("🔍 DIAGNOSTIC: Problèmes de collision avec faces de blocs")
    print("Issue: 'collision détectée mais je rentre dans le bloc sous certaines faces'")
    print()
    
    try:
        # Test 1: Problèmes spécifiques aux faces
        success1 = test_face_specific_collision_issues()
        
        # Test 2: Test systématique
        success2 = test_systematic_collision_detection()
        
        overall_success = success1 and success2
        
        print("\n" + "=" * 60)
        if overall_success:
            print("✅ AUCUN PROBLÈME DE PÉNÉTRATION DÉTECTÉ")
            print("Le système de collision fonctionne correctement.")
        else:
            print("❌ PROBLÈMES DE COLLISION CONFIRMÉS")
            print("Des corrections sont nécessaires pour empêcher la pénétration.")
        
        return overall_success
        
    except Exception as e:
        print(f"\n💥 Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)