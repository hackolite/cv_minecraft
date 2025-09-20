#!/usr/bin/env python3
"""
Démonstration du système de filtrage des logs de collision.
Outil en ligne de commande pour tester différents filtres.
"""

import argparse
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def setup_logging(collision_only=False):
    """Configure le logging selon les options."""
    if collision_only:
        # Ne configurer que le logger de collision
        collision_logger = logging.getLogger('minecraft_collision')
        collision_logger.setLevel(logging.INFO)
        
        # Créer un handler simple sans timestamp pour collision_only
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        collision_logger.addHandler(handler)
        collision_logger.propagate = False
    else:
        # Configuration standard avec tous les loggers
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(message)s'
        )

def run_collision_test(blocks=True, players=True, collision_only=False):
    """Exécute un test de collision avec les filtres spécifiés."""
    
    # Configurer le logging
    setup_logging(collision_only)
    
    # Créer un monde de test
    world = {
        (10, 10, 10): 'stone',
        (15, 12, 8): 'grass'
    }
    
    manager = UnifiedCollisionManager(world)
    
    # Create a simple player class for testing
    class TestPlayer:
        def __init__(self, position, player_id):
            self.position = position
            self.id = player_id
    
    # Ajouter des joueurs fictifs
    players_list = [
        TestPlayer((5, 10, 5), "alice"),
        TestPlayer((20, 10, 20), "bob")
    ]
    manager.set_other_players(players_list)
    
    # Configurer les filtres
    config = {
        "collision_blocks": blocks,
        "collision_players": players,
        "collision_only": collision_only
    }
    manager.configure_collision_logging(config)
    
    print(f"🔧 Configuration: blocs={blocks}, joueurs={players}, collision_only={collision_only}")
    print("-" * 60)
    
    if not collision_only:
        print("📝 Test avec logs système inclus:")
        logging.info("Ceci est un log système normal")
        logging.warning("Ceci est un avertissement système")
    
    print("🧱 Test collision avec bloc:")
    collision1 = manager.check_block_collision((10.5, 10.5, 10.5))
    
    print("\n👥 Test collision entre joueurs:")
    collision2 = manager.check_player_collision((5.3, 10.0, 5.2))
    
    print(f"\nRésultats: collision_bloc={collision1}, collision_joueur={collision2}")
    print("=" * 60)

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Démonstration du filtrage des logs de collision",
        epilog="""
Exemples d'usage:
  %(prog)s --collision-only              # Uniquement les logs de collision
  %(prog)s --no-blocks                   # Pas de logs de collision de blocs
  %(prog)s --no-players                  # Pas de logs de collision de joueurs
  %(prog)s --collision-only --no-players # Uniquement les collisions de blocs
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--no-blocks', action='store_true',
                       help='Désactiver les logs de collision avec blocs')
    parser.add_argument('--no-players', action='store_true',
                       help='Désactiver les logs de collision entre joueurs')
    parser.add_argument('--collision-only', action='store_true',
                       help='Afficher uniquement les logs de collision (pas les logs système)')
    
    args = parser.parse_args()
    
    # Déterminer les paramètres
    blocks = not args.no_blocks
    players = not args.no_players
    collision_only = args.collision_only
    
    print("🚀 DÉMONSTRATION DU FILTRAGE DES LOGS DE COLLISION")
    print("=" * 70)
    
    # Exécuter le test
    run_collision_test(blocks=blocks, players=players, collision_only=collision_only)
    
    print("\n✅ Démonstration terminée")
    
    if collision_only:
        print("💡 Note: Mode 'collision-only' activé - seuls les logs de collision sont affichés")
    
    print("\n🔧 Autres exemples à essayer:")
    print("  python3 demo_collision_filter.py --collision-only")
    print("  python3 demo_collision_filter.py --no-blocks")
    print("  python3 demo_collision_filter.py --no-players")
    print("  python3 demo_collision_filter.py --collision-only --no-players")

if __name__ == "__main__":
    main()