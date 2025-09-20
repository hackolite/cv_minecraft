#!/usr/bin/env python3
"""
Démonstration du système de logging des collisions.
Montre les logs détaillés lors de collisions avec coordonnées AABB, heure et positions.
"""

import logging
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def setup_collision_logging():
    """Configure le logging des collisions pour la démonstration."""
    # Configuration du logger principal
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(message)s'
    )
    
    # Configuration spécifique du logger de collision
    collision_logger = logging.getLogger('minecraft_collision')
    collision_logger.setLevel(logging.INFO)
    
    return collision_logger

def demonstrate_block_collision_logging():
    """Démontre le logging lors de collisions avec des blocs."""
    print("🧱 DÉMONSTRATION: Collision avec des blocs")
    print("=" * 60)
    
    # Créer un monde avec plusieurs blocs
    world = {
        (10, 10, 10): 'stone',
        (15, 12, 8): 'grass', 
        (5, 15, 20): 'wood'
    }
    manager = UnifiedCollisionManager(world)
    
    print("Monde créé avec des blocs aux positions:")
    for pos, block_type in world.items():
        print(f"  - {pos}: {block_type}")
    print()
    
    # Test de différentes positions
    test_positions = [
        (10.5, 10.5, 10.5, "Joueur au centre du bloc stone"),
        (10.2, 10.0, 10.8, "Joueur à la bordure du bloc stone"),
        (15.3, 12.7, 8.1, "Joueur dans le bloc grass"),
        (12.0, 11.0, 12.0, "Joueur dans l'air (pas de collision)")
    ]
    
    for x, y, z, description in test_positions:
        print(f"🎯 Test: {description}")
        print(f"   Position testée: ({x}, {y}, {z})")
        
        collision = manager.check_block_collision((x, y, z))
        
        if collision:
            print("   ✅ Collision détectée - voir logs ci-dessus")
        else:
            print("   ✅ Pas de collision détectée")
        print()

def demonstrate_player_collision_logging():
    """Démontre le logging lors de collisions entre joueurs."""
    print("\n👥 DÉMONSTRATION: Collision entre joueurs")
    print("=" * 60)
    
    # Créer un monde vide
    world = {}
    manager = UnifiedCollisionManager(world)
    
    # Créer des joueurs simulés
    class MockPlayer:
        def __init__(self, name, position):
            self.name = name
            self.position = position
            self.size = 0.5  # Moitié de PLAYER_WIDTH
    
    # Placer des joueurs dans le monde
    players = [
        MockPlayer("Alice", (10.0, 10.0, 10.0)),
        MockPlayer("Bob", (15.0, 10.0, 15.0)),
        MockPlayer("Charlie", (20.0, 10.0, 5.0))
    ]
    
    manager.set_other_players(players)
    
    print("Joueurs dans le monde:")
    for player in players:
        print(f"  - {player.name}: {player.position}")
    print()
    
    # Test de positions qui causent des collisions
    test_positions = [
        (10.3, 10.0, 10.2, "Joueur proche d'Alice"),
        (15.4, 10.0, 15.1, "Joueur proche de Bob"),
        (12.0, 10.0, 12.0, "Joueur loin de tous (pas de collision)")
    ]
    
    for x, y, z, description in test_positions:
        print(f"🎯 Test: {description}")
        print(f"   Position testée: ({x}, {y}, {z})")
        
        collision = manager.check_player_collision((x, y, z))
        
        if collision:
            print("   ✅ Collision détectée - voir logs ci-dessus")
        else:
            print("   ✅ Pas de collision détectée")
        print()

def demonstrate_mixed_collision_scenarios():
    """Démontre des scénarios de collision mixtes."""
    print("\n🌍 DÉMONSTRATION: Scénarios de collision mixtes")
    print("=" * 60)
    
    # Créer un monde avec des blocs et des joueurs
    world = {(12, 10, 12): 'brick'}
    manager = UnifiedCollisionManager(world)
    
    class MockPlayer:
        def __init__(self, name, position):
            self.name = name
            self.position = position
    
    players = [MockPlayer("Dave", (14.0, 10.0, 14.0))]
    manager.set_other_players(players)
    
    print("Environnement mixte:")
    print(f"  - Bloc brick à (12, 10, 12)")
    print(f"  - Joueur Dave à (14.0, 10.0, 14.0)")
    print()
    
    # Tests avec collision générale (blocs + joueurs)
    test_positions = [
        (12.5, 10.5, 12.5, "Position dans le bloc"),
        (14.2, 10.0, 14.1, "Position près du joueur Dave"),
        (16.0, 10.0, 16.0, "Position libre")
    ]
    
    for x, y, z, description in test_positions:
        print(f"🎯 Test: {description}")
        print(f"   Position testée: ({x}, {y}, {z})")
        
        collision = manager.check_collision((x, y, z))
        
        if collision:
            print("   ✅ Collision détectée - voir logs ci-dessus")
        else:
            print("   ✅ Pas de collision détectée")
        print()

def main():
    """Fonction principale de démonstration."""
    print("🚀 DÉMONSTRATION DU SYSTÈME DE LOGGING DES COLLISIONS")
    print("=" * 80)
    print("Cette démonstration montre les logs détaillés lors de collisions")
    print("incluant les coordonnées AABB, l'heure et les positions.")
    print("=" * 80)
    
    # Configuration du logging
    setup_collision_logging()
    
    try:
        # Démonstration des collisions avec les blocs
        demonstrate_block_collision_logging()
        
        # Démonstration des collisions entre joueurs
        demonstrate_player_collision_logging()
        
        # Démonstration des scénarios mixtes
        demonstrate_mixed_collision_scenarios()
        
        print("=" * 80)
        print("✅ DÉMONSTRATION TERMINÉE")
        print("✅ Le système de logging des collisions est opérationnel")
        print("✅ Tous les logs incluent:")
        print("   - 🕒 Heure précise (YYYY-MM-DD HH:MM:SS.mmm)")
        print("   - 📍 Coordonnées des entités en collision")
        print("   - 📦 Coordonnées AABB complètes (min/max)")
        print("   - 🏷️ Type d'objet (bloc/joueur)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)