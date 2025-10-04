#!/usr/bin/env python3
"""
Test collision logging functionality.
Vérifie que les logs de collision incluent bien les coordonnées AABB, l'heure et les positions.
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
    collision_logger.addHandler(handler)
    
    return log_capture, collision_logger

def test_block_collision_logging():
    """Test block collision logging."""
    print("🧪 Test des logs de collision avec les blocs")
    
    # Setup logging capture
    log_capture, collision_logger = setup_logging_capture()
    
    # Create a world with a single block
    world = {(10, 10, 10): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Test collision that should trigger logging
    position = (10.5, 10.5, 10.5)  # Position inside the block
    collision = manager.check_block_collision(position)
    
    # Check results
    assert collision == True, "Should detect collision"
    
    # Get captured logs
    log_output = log_capture.getvalue()
    print("Logs capturés:")
    print(log_output)
    
    # Verify log content
    assert "COLLISION DÉTECTÉE - Bloc" in log_output, "Should log collision detection"
    assert "Heure:" in log_output, "Should log time"
    assert "Position joueur:" in log_output, "Should log player position"
    assert "Position bloc:" in log_output, "Should log block position"
    assert "AABB Joueur:" in log_output, "Should log player AABB"
    assert "AABB Bloc:" in log_output, "Should log block AABB"
    assert "(10.500, 10.500, 10.500)" in log_output, "Should log exact player position"
    assert "(10, 10, 10)" in log_output, "Should log block position"
    
    print("✅ Test de collision bloc: RÉUSSI")
    return True

def test_player_collision_logging():
    """Test player collision logging."""
    print("\n🧪 Test des logs de collision entre joueurs")
    
    # Setup logging capture
    log_capture, collision_logger = setup_logging_capture()
    
    # Create empty world
    world = {}
    manager = UnifiedCollisionManager(world)
    
    # Create a mock player object
    class MockPlayer:
        def __init__(self, position):
            self.position = position
            self.size = 0.5  # Half of PLAYER_WIDTH
    
    # Set up other players
    other_player = MockPlayer((10.3, 10.0, 10.0))  # Close position that should cause collision
    manager.set_other_players([other_player])
    
    # Test collision
    position = (10.0, 10.0, 10.0)
    collision = manager.check_player_collision(position)
    
    # Check results
    assert collision == True, "Should detect player collision"
    
    # Get captured logs
    log_output = log_capture.getvalue()
    print("Logs capturés:")
    print(log_output)
    
    # Verify log content
    assert "COLLISION DÉTECTÉE - Joueur vs Joueur" in log_output, "Should log player collision"
    assert "Heure:" in log_output, "Should log time"
    assert "Position joueur 1:" in log_output, "Should log first player position"
    assert "Position joueur 2:" in log_output, "Should log second player position"
    assert "AABB Joueur 1:" in log_output, "Should log first player AABB"
    assert "AABB Joueur 2:" in log_output, "Should log second player AABB"
    
    print("✅ Test de collision joueur: RÉUSSI")
    return True

def test_no_collision_no_logs():
    """Test that no collision means no logs."""
    print("\n🧪 Test qu'aucune collision = aucun log")
    
    # Setup logging capture
    log_capture, collision_logger = setup_logging_capture()
    
    # Create empty world
    world = {}
    manager = UnifiedCollisionManager(world)
    
    # Test position with no collision
    position = (10.0, 10.0, 10.0)
    collision = manager.check_block_collision(position)
    
    # Check results
    assert collision == False, "Should not detect collision"
    
    # Get captured logs
    log_output = log_capture.getvalue()
    print(f"Logs capturés (devrait être vide): '{log_output}'")
    
    # Verify no logs
    assert log_output.strip() == "", "Should not log when no collision"
    
    print("✅ Test aucune collision: RÉUSSI")
    return True

def main():
    """Run all collision logging tests."""
    print("🚀 Tests de logging des collisions - Minecraft CV")
    print("=" * 80)
    
    try:
        # Test block collision logging
        test_block_collision_logging()
        
        # Test player collision logging  
        test_player_collision_logging()
        
        # Test no collision scenario
        test_no_collision_no_logs()
        
        print("\n" + "=" * 80)
        print("✅ TOUS LES TESTS PASSENT!")
        print("✅ Le système de logging des collisions fonctionne correctement")
        print("✅ Les logs incluent les coordonnées AABB, l'heure et les positions")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)