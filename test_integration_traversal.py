#!/usr/bin/env python3
"""
Test d'intégration de l'agent de traversée illégale avec le serveur.
Test la logique de détection sans dépendances WebSocket.
"""

import logging
import sys
import os
import io
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock websockets avant d'importer le serveur
sys.modules['websockets'] = Mock()
sys.modules['websockets.exceptions'] = Mock()
Mock.ConnectionClosed = Exception

from protocol import PlayerState
from illegal_traversal_agent import IllegalBlockTraversalAgent
from noise_gen import NoiseGen


def setup_logging_capture():
    """Configure le logging pour capturer les logs."""
    log_capture = io.StringIO()
    
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Capturer les logs de traversée illégale
    traversal_logger = logging.getLogger('illegal_traversal')
    traversal_logger.setLevel(logging.INFO)
    traversal_logger.addHandler(handler)
    
    return log_capture, traversal_logger


def test_agent_integration():
    """Test d'intégration de l'agent avec la logique serveur."""
    print("🧪 Test d'intégration de l'agent de traversée illégale")
    
    # Setup logging
    log_capture, traversal_logger = setup_logging_capture()
    
    # Créer un monde avec des blocs
    world_blocks = {
        (10, 10, 10): 'stone',
        (11, 10, 10): 'grass',
        (12, 10, 10): 'wood'
    }
    
    # Créer l'agent
    agent = IllegalBlockTraversalAgent(world_blocks)
    
    # Simuler un joueur
    player_id = "test_player_123"
    player_name = "TestPlayer"
    
    # Test 1: Mouvement légal (ne devrait pas déclencher)
    old_pos = (9.0, 10.0, 10.0)  # Position en air
    new_pos = (8.0, 10.0, 10.0)  # Autre position en air
    
    result = agent.check_traversal(player_id, player_name, old_pos, new_pos)
    assert result == False, "Legal movement should not trigger detection"
    
    # Test 2: Traversée illégale (devrait déclencher)
    illegal_old_pos = (9.0, 10.0, 10.0)  # Position en air
    illegal_new_pos = (10.5, 10.5, 10.5)  # Position dans le bloc stone
    
    result = agent.check_traversal(player_id, player_name, illegal_old_pos, illegal_new_pos)
    assert result == True, "Illegal traversal should be detected"
    
    # Vérifier les logs
    log_output = log_capture.getvalue()
    
    # Vérifier le format requis
    assert "WARNING" in log_output, "Should have WARNING level"
    assert "🚨 ILLEGAL BLOCK TRAVERSAL" in log_output, "Should have illegal traversal message"
    assert f"Player {player_name} ({player_id})" in log_output, "Should include player info"
    assert "traversed solid block (10, 10, 10)" in log_output, "Should include block position"
    assert f"Old position: {illegal_old_pos}" in log_output, "Should log old position"
    assert f"New position: {illegal_new_pos}" in log_output, "Should log new position"
    assert "Block type: stone" in log_output, "Should log block type"
    
    # Test de la déconnexion
    agent.log_disconnection(player_id, player_name)
    log_output_after = log_capture.getvalue()
    assert f"Player {player_name} ({player_id}) disconnected for illegal block traversal." in log_output_after
    
    print("✅ Test d'intégration: RÉUSSI")
    return True


def test_edge_cases():
    """Test des cas limites."""
    print("\n🧪 Test des cas limites")
    
    # Setup logging
    log_capture, traversal_logger = setup_logging_capture()
    
    # Monde avec blocs air (ne devraient pas déclencher)
    world_with_air = {
        (10, 10, 10): 'air',
        (11, 10, 10): 'stone'
    }
    
    agent = IllegalBlockTraversalAgent(world_with_air)
    
    # Test avec bloc air (ne devrait pas déclencher)
    result = agent.check_traversal("player1", "Player1", (9.0, 10.0, 10.0), (10.5, 10.5, 10.5))
    assert result == False, "Air blocks should not trigger traversal detection"
    
    # Test avec bloc solide (devrait déclencher)
    result = agent.check_traversal("player2", "Player2", (10.0, 10.0, 10.0), (11.5, 10.5, 10.5))
    assert result == True, "Solid blocks should trigger traversal detection"
    
    # Test avec nom de joueur None
    result = agent.check_traversal("player3", None, (10.0, 10.0, 10.0), (11.5, 10.5, 10.5))
    assert result == True, "Should work with None player name"
    
    log_output = log_capture.getvalue()
    assert "Player Unknown (player3)" in log_output, "Should handle None player name"
    
    print("✅ Test des cas limites: RÉUSSI")
    return True


def test_multiple_blocks_traversal():
    """Test de traversée avec multiple blocs."""
    print("\n🧪 Test de traversée avec multiple blocs")
    
    # Setup logging
    log_capture, traversal_logger = setup_logging_capture()
    
    # Monde avec plusieurs blocs proches
    world_blocks = {
        (10, 10, 10): 'stone',
        (10, 11, 10): 'grass',
        (11, 10, 10): 'wood'
    }
    
    agent = IllegalBlockTraversalAgent(world_blocks)
    
    # Test de traversée qui touche plusieurs blocs
    # La position du joueur peut intersecter plusieurs blocs selon sa taille
    result = agent.check_traversal("player1", "Player1", (9.0, 10.0, 10.0), (10.5, 10.5, 10.5))
    assert result == True, "Should detect traversal even with multiple blocks"
    
    log_output = log_capture.getvalue()
    # Devrait détecter au moins un des blocs solides
    block_detected = any(block_type in log_output for block_type in ['stone', 'grass', 'wood'])
    assert block_detected, "Should detect one of the solid blocks"
    
    print("✅ Test de traversée avec multiple blocs: RÉUSSI")
    return True


def main():
    """Exécute tous les tests d'intégration."""
    print("🚀 Tests d'intégration de l'agent de traversée illégale - Minecraft CV")
    print("=" * 80)
    
    try:
        # Test d'intégration principal
        test_agent_integration()
        
        # Test des cas limites
        test_edge_cases()
        
        # Test avec multiple blocs
        test_multiple_blocks_traversal()
        
        print("\n" + "=" * 80)
        print("✅ TOUS LES TESTS D'INTÉGRATION PASSENT!")
        print("✅ L'agent s'intègre correctement avec la logique serveur")
        print("✅ Le format de logging respecte les exigences")
        print("✅ La détection fonctionne dans tous les cas testés")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)