#!/usr/bin/env python3
"""
Test cube position validation functionality.
Tests the simple position checking to avoid cube position conflicts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState
from minecraft_physics import check_cube_position_occupied, MinecraftCollisionDetector


def test_cube_position_occupied():
    """Test the basic cube position occupied check."""
    print("🧪 Testing cube position occupied check...")
    
    # Test no collision - cubes far apart
    position1 = (0, 0, 0)
    position2 = (5, 0, 0)  # 5 units apart, should not conflict
    
    player1 = PlayerState("player1", position1, (0, 0), "Player1")
    player2 = PlayerState("player2", position2, (0, 0), "Player2")
    
    # Test position1 against player2
    occupied = check_cube_position_occupied(position1, 0.4, [player2])
    assert not occupied, "Position should not be occupied when cubes are far apart"
    print("✅ No position conflict for distant cubes")
    
    # Test collision - cubes close together
    position3 = (0.5, 0, 0)  # Very close to position1
    player3 = PlayerState("player3", position3, (0, 0), "Player3")
    
    occupied = check_cube_position_occupied(position1, 0.4, [player3])
    assert occupied, "Position should be occupied when cubes are close together"
    print("✅ Position conflict detected for overlapping cubes")
    
    # Test edge case - cubes just touching
    position4 = (0.8, 0, 0)  # Right at edge of collision boundary
    player4 = PlayerState("player4", position4, (0, 0), "Player4")
    
    occupied = check_cube_position_occupied(position1, 0.4, [player4])
    assert occupied, "Position should be occupied when cubes are touching"
    print("✅ Position conflict detected for touching cubes")
    
    # Test multiple cubes - one conflict
    cubes = [player2, player3, player4]  # player2 far, player3 & player4 close
    occupied = check_cube_position_occupied(position1, 0.4, cubes)
    assert occupied, "Should detect position conflict with at least one cube"
    print("✅ Position conflict detected with multiple cubes")
    
    # Test multiple cubes - no conflict
    far_cubes = [player2]  # Only far cube
    occupied = check_cube_position_occupied(position1, 0.4, far_cubes)
    assert not occupied, "Should not detect position conflict with only distant cubes"
    print("✅ No position conflict with only distant cubes")
    
    # Test Y-axis conflict
    position5 = (0, 0.5, 0)  # Above position1
    player5 = PlayerState("player5", position5, (0, 0), "Player5")
    
    occupied = check_cube_position_occupied(position1, 0.4, [player5])
    assert occupied, "Cubes should conflict on Y-axis too"
    print("✅ Y-axis position conflict detected")
    
    # Test Z-axis conflict
    position6 = (0, 0, 0.5)  # In front of position1
    player6 = PlayerState("player6", position6, (0, 0), "Player6")
    
    occupied = check_cube_position_occupied(position1, 0.4, [player6])
    assert occupied, "Cubes should conflict on Z-axis too"
    print("✅ Z-axis position conflict detected")
    
    # Test with invalid cube objects
    invalid_cubes = [None, {}, "not_a_cube"]
    occupied = check_cube_position_occupied(position1, 0.4, invalid_cubes)
    assert not occupied, "Should handle invalid cube objects gracefully"
    print("✅ Invalid cube objects handled gracefully")
    
    return True


def test_collision_detector_integration():
    """Test integration with MinecraftCollisionDetector."""
    print("\n🧪 Testing collision detector integration...")
    
    # Create a collision detector with no world blocks
    world_blocks = {}
    detector = MinecraftCollisionDetector(world_blocks)
    
    # Set up other cubes
    position1 = (0, 0, 0)
    position2 = (0.5, 0, 0)  # Close to position1
    
    player2 = PlayerState("player2", position2, (0, 0), "Player2")
    detector.set_other_cubes([player2])
    
    # Test collision detection - should detect cube collision
    collision = detector.check_collision(position1)
    assert collision, "Should detect collision with other cube"
    print("✅ Collision detector detects cube position conflicts")
    
    # Test with distant cube
    position3 = (10, 0, 0)  # Far from position1
    player3 = PlayerState("player3", position3, (0, 0), "Player3")
    detector.set_other_cubes([player3])
    
    collision = detector.check_collision(position1)
    assert not collision, "Should not detect collision with distant cube"
    print("✅ Collision detector allows distant cube positions")
    
    # Test with no other cubes
    detector.set_other_cubes([])
    collision = detector.check_collision(position1)
    assert not collision, "Should not detect collision with no other cubes"
    print("✅ Collision detector works with no other cubes")
    
    # Test with world blocks and cubes
    world_blocks = {(0, -1, 0): "stone"}  # Block below position1
    detector = MinecraftCollisionDetector(world_blocks)
    detector.set_other_cubes([player2])
    
    collision = detector.check_collision(position1)
    assert collision, "Should detect cube collision even with world blocks present"
    print("✅ Cube collision detection works alongside block collision")
    
    return True


def test_integration_with_client_code():
    """Test integration with client collision logic."""
    print("\n🧪 Testing integration with client collision logic...")
    
    # Simulate what happens in the client collide method
    class MockModel:
        def __init__(self):
            self.world = {}  # No blocks
        
        def get_other_cubes(self):
            # Return a cube that would cause collision
            player = PlayerState("other", (0.5, 0, 0), (0, 0), "Other")
            return [player]
    
    # Test the collision logic similar to what's in minecraft_client_fr.py
    model = MockModel()
    position = (0, 0, 0)
    
    # Create collision detector and set other cubes
    collision_detector = MinecraftCollisionDetector(model.world)
    other_cubes = model.get_other_cubes()
    collision_detector.set_other_cubes(other_cubes)
    
    # Check collision
    collision = collision_detector.check_collision(position)
    assert collision, "Client integration should detect cube conflicts"
    print("✅ Client integration detects cube position conflicts")
    
    # Test with distant position
    distant_position = (10, 0, 0)
    collision = collision_detector.check_collision(distant_position)
    assert not collision, "Client integration should allow distant positions"
    print("✅ Client integration allows valid positions")
    
    return True


if __name__ == "__main__":
    print("🎮 Testing Cube Position Validation System\n")
    
    try:
        success = True
        success &= test_cube_position_occupied()
        success &= test_collision_detector_integration()
        success &= test_integration_with_client_code()
        
        if success:
            print("\n🎉 ALL CUBE POSITION VALIDATION TESTS PASSED!")
            print("✅ Simple cube position checking works correctly")
            print("✅ Prevents cubes from occupying same positions")
            print("✅ Avoids complex collision calculations when possible")
            print("✅ Integrates seamlessly with existing collision system")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)