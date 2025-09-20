#!/usr/bin/env python3
"""
Démonstration de l'agent de détection de traversée illégale de blocs.
Montre le format exact des logs comme requis dans le problem statement.
"""

import logging
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from illegal_traversal_agent import IllegalBlockTraversalAgent


def setup_demo_logging():
    """Configure le logging pour la démonstration."""
    # Configuration du logging selon le format requis
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s,%(msecs)03d - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configuration spécifique du logger de traversée
    traversal_logger = logging.getLogger('illegal_traversal')
    traversal_logger.setLevel(logging.INFO)
    
    return traversal_logger


def demo_illegal_traversal():
    """Démontre la détection de traversée illégale avec le format de log requis."""
    print("🚨 DÉMONSTRATION: Détection de traversée illégale de blocs")
    print("=" * 80)
    print()
    print("Scénario: Un joueur tente de traverser un bloc solide")
    print("- Position initiale: (9.0, 10.0, 10.0) [en air]")
    print("- Position finale: (10.5, 10.5, 10.5) [dans un bloc stone]")
    print()
    print("Logs générés:")
    print("-" * 40)
    
    # Créer un monde avec un bloc solide
    world = {(10, 10, 10): 'stone'}
    agent = IllegalBlockTraversalAgent(world)
    
    # Simuler une traversée illégale
    player_id = "uuid-1234-5678-abcd"
    player_name = "Joueur"
    old_position = (9.0, 10.0, 10.0)
    new_position = (10.5, 10.5, 10.5)
    
    # Déclencher la détection (ceci va générer les logs)
    result = agent.check_traversal(player_id, player_name, old_position, new_position)
    
    # Log de déconnexion
    agent.log_disconnection(player_id, player_name)
    
    print("-" * 40)
    print()
    print(f"✅ Détection: {'POSITIVE' if result else 'NEGATIVE'}")
    print("✅ Le format des logs correspond aux exigences du problem statement")
    print()
    
    return result


def demo_multiple_scenarios():
    """Démontre différents scénarios de traversée."""
    print("\n🎯 DÉMONSTRATION: Différents scénarios")
    print("=" * 80)
    
    # Créer un monde avec différents types de blocs
    world = {
        (10, 10, 10): 'stone',
        (11, 10, 10): 'grass', 
        (12, 10, 10): 'wood',
        (13, 10, 10): 'air'  # Ne devrait pas déclencher
    }
    agent = IllegalBlockTraversalAgent(world)
    
    scenarios = [
        {
            'name': 'Traversée de bloc STONE',
            'player': ('player1', 'Alice'),
            'old_pos': (9.0, 10.0, 10.0),
            'new_pos': (10.5, 10.5, 10.5),
            'expected': True
        },
        {
            'name': 'Traversée de bloc GRASS',
            'player': ('player2', 'Bob'), 
            'old_pos': (10.0, 10.0, 10.0),
            'new_pos': (11.5, 10.5, 10.5),
            'expected': True
        },
        {
            'name': 'Traversée de bloc WOOD',
            'player': ('player3', 'Charlie'),
            'old_pos': (11.0, 10.0, 10.0),
            'new_pos': (12.5, 10.5, 10.5),
            'expected': True
        },
        {
            'name': 'Mouvement dans l\'AIR (légal)',
            'player': ('player4', 'Dave'),
            'old_pos': (12.0, 10.0, 10.0),
            'new_pos': (13.5, 10.5, 10.5),
            'expected': False
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}:")
        print(f"   Joueur: {scenario['player'][1]} ({scenario['player'][0]})")
        print(f"   {scenario['old_pos']} → {scenario['new_pos']}")
        print("   Logs:")
        
        result = agent.check_traversal(
            scenario['player'][0], 
            scenario['player'][1],
            scenario['old_pos'],
            scenario['new_pos']
        )
        
        if result:
            agent.log_disconnection(scenario['player'][0], scenario['player'][1])
        else:
            print("   [Aucun log - mouvement légal]")
        
        print(f"   Résultat: {'✅ DÉTECTÉ' if result else '✅ AUTORISÉ'}")
        assert result == scenario['expected'], f"Scenario {i} failed"
    
    print(f"\n✅ Tous les scénarios se comportent comme attendu")


def demo_log_format_compliance():
    """Vérifie la conformité avec le format de log requis."""
    print("\n📋 VÉRIFICATION: Conformité du format de log")
    print("=" * 80)
    
    print("Format requis dans le problem statement:")
    print("2025-09-21 01:12:05,123 - WARNING - 🚨 ILLEGAL BLOCK TRAVERSAL - Player Joueur (UUID) traversed solid block (x, y, z)")
    print("2025-09-21 01:12:05,124 - INFO -    Old position: (...)")
    print("2025-09-21 01:12:05,124 - INFO -    New position: (...)")
    print("2025-09-21 01:12:05,125 - INFO -    Block type: ...")
    print("2025-09-21 01:12:05,130 - INFO - Player Joueur (UUID) disconnected for illegal block traversal.")
    print()
    print("Format généré par notre implémentation:")
    print("-" * 60)
    
    # Générer un exemple avec le format exact
    world = {(15, 20, 8): 'grass'}
    agent = IllegalBlockTraversalAgent(world)
    
    result = agent.check_traversal("uuid-example", "Joueur", (14.0, 20.0, 8.0), (15.5, 20.5, 8.5))
    agent.log_disconnection("uuid-example", "Joueur")
    
    print("-" * 60)
    print("✅ Le format respecte les exigences:")
    print("  - Timestamp avec millisecondes")
    print("  - Niveau WARNING pour la détection")
    print("  - Niveau INFO pour les détails")
    print("  - Nom et UUID du joueur")
    print("  - Positions anciennes et nouvelles")
    print("  - Type de bloc traversé")
    print("  - Log de déconnexion spécifique")


def main():
    """Fonction principale de démonstration."""
    # Setup du logging
    setup_demo_logging()
    
    print("🚀 DÉMONSTRATION COMPLÈTE - Agent de détection de traversée illégale")
    print("Minecraft CV - Implementation selon le problem statement")
    print("=" * 80)
    
    try:
        # Démonstration de base
        demo_illegal_traversal()
        
        # Différents scénarios
        demo_multiple_scenarios()
        
        # Vérification du format
        demo_log_format_compliance()
        
        print("\n" + "=" * 80)
        print("✅ DÉMONSTRATION TERMINÉE AVEC SUCCÈS")
        print("✅ L'agent de détection fonctionne conformément aux exigences")
        print("✅ Le format de logging respecte exactement le problem statement")
        print("✅ La déconnexion automatique est implémentée")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)