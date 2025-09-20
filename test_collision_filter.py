#!/usr/bin/env python3
"""
Test du système de filtrage des logs de collision.
Vérifie que le filtrage fonctionne correctement pour différents types de logs.
"""

import logging
import sys
import os
import io
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def setup_logging_capture():
    """Setup logging to capture collision logs for testing."""
    # Create a string buffer to capture logs
    log_capture = io.StringIO()
    
    # Create a handler for the collision logger
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    
    # Get the collision logger and add our handler
    collision_logger = logging.getLogger('minecraft_collision')
    collision_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid interference
    collision_logger.handlers.clear()
    collision_logger.addHandler(handler)
    collision_logger.propagate = False
    
    return log_capture, collision_logger

def test_collision_only_filter():
    """Test le filtre collision_only."""
    print("🧪 Test du filtre collision_only")
    
    # Setup logging capture for collision logger specifically
    log_capture = io.StringIO()
    
    # Create a handler for the collision logger
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    
    # Get the collision logger and add our handler
    collision_logger = logging.getLogger('minecraft_collision')
    collision_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid interference
    collision_logger.handlers.clear()
    collision_logger.addHandler(handler)
    collision_logger.propagate = False
    
    # Create world and manager
    world = {(10, 10, 10): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Test 1: collision_blocks = True (devrait permettre les logs de bloc)
    config = {"collision_only": True, "collision_blocks": True, "collision_players": True}
    manager.configure_collision_logging(config)
    
    # Test collision de bloc
    manager.check_block_collision((10.5, 10.5, 10.5))
    output1 = log_capture.getvalue()
    
    # Reset capture
    log_capture.seek(0)
    log_capture.truncate(0)
    
    # Test 2: collision_blocks = False (ne devrait pas permettre les logs de bloc)
    config = {"collision_only": True, "collision_blocks": False, "collision_players": True}
    manager.configure_collision_logging(config)
    
    # Test collision de bloc (ne devrait pas apparaître)
    manager.check_block_collision((10.5, 10.5, 10.5))
    output2 = log_capture.getvalue()
    
    # Vérifications
    assert "COLLISION DÉTECTÉE" in output1, "Collision log should appear with collision_blocks=True"
    assert output2.strip() == "", "Collision log should NOT appear with collision_blocks=False"
    
    print("✅ Test collision_only: RÉUSSI")
    return True

def test_block_filter():
    """Test le filtre collision_blocks."""
    print("🧪 Test du filtre collision_blocks")
    
    # Setup logging capture
    log_capture, collision_logger = setup_logging_capture()
    
    # Create world and manager
    world = {(10, 10, 10): 'stone'}
    manager = UnifiedCollisionManager(world)
    manager.set_other_players([{"position": (15, 10, 15), "id": "test_player"}])
    
    # Test 1: collision_blocks = True
    config = {"collision_only": True, "collision_blocks": True, "collision_players": True}
    manager.configure_collision_logging(config)
    
    manager.check_block_collision((10.5, 10.5, 10.5))
    output1 = log_capture.getvalue()
    
    # Reset capture
    log_capture.seek(0)
    log_capture.truncate(0)
    
    # Test 2: collision_blocks = False
    config = {"collision_only": True, "collision_blocks": False, "collision_players": True}
    manager.configure_collision_logging(config)
    
    manager.check_block_collision((10.5, 10.5, 10.5))
    output2 = log_capture.getvalue()
    
    # Vérifications
    assert "COLLISION DÉTECTÉE - Bloc" in output1, "Block collision should appear when enabled"
    assert output2.strip() == "", "Block collision should NOT appear when disabled"
    
    print("✅ Test collision_blocks: RÉUSSI")
    return True

def test_player_filter():
    """Test le filtre collision_players."""
    print("🧪 Test du filtre collision_players")
    
    # Setup logging capture
    log_capture, collision_logger = setup_logging_capture()
    
    # Create a simple player class for testing
    class TestPlayer:
        def __init__(self, position, player_id):
            self.position = position
            self.id = player_id
    
    # Create world and manager
    world = {}
    manager = UnifiedCollisionManager(world)
    test_player = TestPlayer((10, 10, 10), "test_player")
    manager.set_other_players([test_player])
    
    # Test 1: collision_players = True
    config = {"collision_only": True, "collision_blocks": True, "collision_players": True}
    manager.configure_collision_logging(config)
    
    manager.check_player_collision((10.3, 10.0, 10.0))
    output1 = log_capture.getvalue()
    
    # Reset capture
    log_capture.seek(0)
    log_capture.truncate(0)
    
    # Test 2: collision_players = False
    config = {"collision_only": True, "collision_blocks": True, "collision_players": False}
    manager.configure_collision_logging(config)
    
    manager.check_player_collision((10.3, 10.0, 10.0))
    output2 = log_capture.getvalue()
    
    # Vérifications
    assert "COLLISION DÉTECTÉE - Joueur vs Joueur" in output1, "Player collision should appear when enabled"
    assert output2.strip() == "", "Player collision should NOT appear when disabled"
    
    print("✅ Test collision_players: RÉUSSI")
    return True

def test_mixed_filtering():
    """Test des combinaisons de filtres."""
    print("🧪 Test des combinaisons de filtres")
    
    # Setup logging capture
    log_capture, collision_logger = setup_logging_capture()
    
    # Create a simple player class for testing
    class TestPlayer:
        def __init__(self, position, player_id):
            self.position = position
            self.id = player_id
    
    # Create world and manager
    world = {(10, 10, 10): 'stone'}
    manager = UnifiedCollisionManager(world)
    test_player = TestPlayer((15, 10, 15), "test_player")
    manager.set_other_players([test_player])
    
    # Test: Seulement les blocs, pas les joueurs
    config = {"collision_only": True, "collision_blocks": True, "collision_players": False}
    manager.configure_collision_logging(config)
    
    # Test les deux types de collision
    manager.check_block_collision((10.5, 10.5, 10.5))
    manager.check_player_collision((15.2, 10.0, 15.1))
    
    output = log_capture.getvalue()
    
    # Vérifications
    assert "COLLISION DÉTECTÉE - Bloc" in output, "Block collision should appear"
    assert "COLLISION DÉTECTÉE - Joueur vs Joueur" not in output, "Player collision should NOT appear"
    
    print("✅ Test combinaisons de filtres: RÉUSSI")
    return True

def main():
    """Run all collision filtering tests."""
    print("🚀 Tests de filtrage des logs de collision - Minecraft CV")
    print("=" * 80)
    
    try:
        # Test collision_only filter
        test_collision_only_filter()
        
        # Test block filter  
        test_block_filter()
        
        # Test player filter
        test_player_filter()
        
        # Test mixed filtering
        test_mixed_filtering()
        
        print("\n" + "=" * 80)
        print("✅ TOUS LES TESTS DE FILTRAGE PASSENT!")
        print("✅ Le système de filtrage des logs de collision fonctionne correctement")
        print("✅ Les filtres collision_only, collision_blocks et collision_players fonctionnent")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)