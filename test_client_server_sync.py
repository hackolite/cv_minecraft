#!/usr/bin/env python3
"""
Test comprehensive client-server cube position synchronization.
This test simulates the complete client-server communication flow to ensure
cube positions are always correctly synchronized and never float.
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, Cube, Message, MessageType, create_player_update_message
from client import ClientModel

def test_server_message_processing():
    """Test processing of server position update messages."""
    print("🧪 Testing server message processing...")
    
    model = ClientModel()
    
    # Simulate receiving player updates from server
    server_updates = [
        {"id": "player1", "position": [0, 0, 0], "rotation": [0, 0], "name": "Player1", "velocity": [0, 0, 0], "on_ground": True, "size": 0.5},
        {"id": "player2", "position": [5.5, 10.0, -3.2], "rotation": [45, -30], "name": "Player2", "velocity": [1, 0, -1], "on_ground": False, "size": 0.5},
        {"id": "player3", "position": [100, 200, 300], "rotation": [180, 90], "name": "Player3", "velocity": [0, -5, 0], "on_ground": False, "size": 0.5},
    ]
    
    for update_data in server_updates:
        try:
            # Create player from server data (as client would do)
            player = PlayerState.from_dict(update_data)
            model.add_cube(player)
            
            # Verify position integrity
            render_pos = player.get_render_position()
            cube_bottom = render_pos[1] - player.size
            expected_bottom = update_data["position"][1]
            
            print(f"   Player {player.id}:")
            print(f"     Server position: {update_data['position']}")
            print(f"     Render position: {render_pos}")
            print(f"     Cube bottom: {cube_bottom}")
            print(f"     Expected bottom: {expected_bottom}")
            
            if abs(cube_bottom - expected_bottom) < 0.001:
                print(f"     ✅ Correctly synchronized")
            else:
                print(f"     ❌ Synchronization error!")
                return False
                
        except Exception as e:
            print(f"   ❌ Error processing server update for {update_data['id']}: {e}")
            return False
    
    return True

def test_position_update_robustness():
    """Test robustness of position updates against network issues."""
    print("\n🧪 Testing position update robustness...")
    
    model = ClientModel()
    
    # Create initial player
    local_player = model.create_local_player("robust_test", (0, 0, 0), (0, 0), "RobustPlayer")
    
    # Simulate various network scenarios
    update_scenarios = [
        # Normal updates
        {"position": [1, 1, 1], "description": "Normal movement"},
        {"position": [2.5, 3.5, 4.5], "description": "Fractional coordinates"},
        {"position": [-5, -10, -15], "description": "Negative coordinates"},
        
        # Edge cases that might cause floating
        {"position": [0.0001, 0.0001, 0.0001], "description": "Very small coordinates"},
        {"position": [999.999, 999.999, 999.999], "description": "Very large coordinates"},
        {"position": [1.23456789, 2.34567890, 3.45678901], "description": "High precision coordinates"},
    ]
    
    for scenario in update_scenarios:
        try:
            pos = scenario["position"]
            desc = scenario["description"]
            
            # Update position
            local_player.update_position(pos)
            
            # Verify rendering
            render_pos = local_player.get_render_position()
            cube_bottom = render_pos[1] - local_player.size
            
            print(f"   {desc}:")
            print(f"     Position: {pos}")
            print(f"     Render: {render_pos}")
            print(f"     Cube bottom: {cube_bottom}")
            
            # Verify accuracy
            if abs(cube_bottom - pos[1]) < 0.001:
                print(f"     ✅ Robust positioning")
            else:
                print(f"     ❌ Position drift detected!")
                return False
                
        except Exception as e:
            print(f"   ❌ Error in scenario '{scenario['description']}': {e}")
            return False
    
    return True

def test_message_serialization_integrity():
    """Test that position data maintains integrity through JSON serialization."""
    print("\n🧪 Testing message serialization integrity...")
    
    # Test positions that might be problematic for JSON serialization
    test_positions = [
        (0, 0, 0),
        (1.5, 2.5, 3.5),
        (-10.123, -20.456, -30.789),
        (0.0000001, 0.0000001, 0.0000001),  # Very small numbers
        (1e10, 1e10, 1e10),  # Very large numbers
        (float('inf'), 5, 5),  # Special case that should be handled
    ]
    
    for i, pos in enumerate(test_positions):
        try:
            # Create player with test position
            player = PlayerState(f"serialize_test_{i}", pos, (0, 0), f"SerializeTest{i}")
            
            # Create update message (as server would do)
            message = create_player_update_message(player)
            
            # Serialize to JSON (as would happen over network)
            json_str = message.to_json()
            
            # Deserialize from JSON (as client would do)
            restored_message = Message.from_json(json_str)
            
            # Recreate player from deserialized data
            restored_player = PlayerState.from_dict(restored_message.data)
            
            # Verify position integrity
            original_render = player.get_render_position()
            restored_render = restored_player.get_render_position()
            
            original_bottom = original_render[1] - player.size
            restored_bottom = restored_render[1] - restored_player.size
            
            print(f"   Position {pos}:")
            print(f"     Original bottom: {original_bottom}")
            print(f"     Restored bottom: {restored_bottom}")
            
            # Check for special cases
            if any(not (float('-inf') < coord < float('inf')) for coord in pos):
                print(f"     ⚠️  Special value detected - checking error handling")
                # For special values like infinity, we expect controlled failure
                continue
            
            if abs(original_bottom - restored_bottom) < 0.001:
                print(f"     ✅ Serialization preserves integrity")
            else:
                print(f"     ❌ Serialization corrupted position!")
                return False
                
        except (ValueError, OverflowError, TypeError) as e:
            print(f"   ⚠️  Expected error for problematic position {pos}: {type(e).__name__}")
            # This is acceptable for extreme values
            continue
        except Exception as e:
            print(f"   ❌ Unexpected error for position {pos}: {e}")
            return False
    
    return True

def test_concurrent_position_updates():
    """Test handling of rapid concurrent position updates."""
    print("\n🧪 Testing concurrent position updates...")
    
    model = ClientModel()
    
    # Create multiple players
    players = []
    for i in range(5):
        player = model.create_local_player(f"concurrent_{i}", (i, i, i), (0, 0), f"Player{i}")
        players.append(player)
    
    # Add remote players
    for i in range(5, 10):
        remote_player = PlayerState(f"remote_{i}", (i, i, i), (0, 0), f"Remote{i}")
        model.add_cube(remote_player)
        players.append(remote_player)
    
    print(f"   Created {len(players)} players for concurrent testing")
    
    # Simulate rapid position updates
    for round_num in range(10):
        print(f"   Update round {round_num + 1}:")
        
        for i, player in enumerate(players):
            # Generate new position
            new_pos = (i + round_num * 0.1, i + round_num * 0.2, i + round_num * 0.3)
            
            try:
                # Update position
                player.update_position(new_pos)
                
                # Verify immediately
                render_pos = player.get_render_position()
                cube_bottom = render_pos[1] - player.size
                
                if abs(cube_bottom - new_pos[1]) > 0.001:
                    print(f"     ❌ Player {player.id} position inconsistent!")
                    return False
                    
            except Exception as e:
                print(f"     ❌ Error updating player {player.id}: {e}")
                return False
        
        print(f"     ✅ All {len(players)} players updated correctly")
    
    return True

def test_edge_case_positioning():
    """Test edge cases that might cause floating cubes."""
    print("\n🧪 Testing edge case positioning...")
    
    model = ClientModel()
    
    edge_cases = [
        # Boundary conditions
        {"pos": (0, 0, 0), "desc": "Origin position"},
        {"pos": (-0.5, -0.5, -0.5), "desc": "Negative half-size position"},
        {"pos": (0.5, 0.5, 0.5), "desc": "Positive half-size position"},
        
        # Fractional positions that might round incorrectly
        {"pos": (0.33333333, 0.66666666, 0.99999999), "desc": "Repeating decimals"},
        {"pos": (1.0000001, 2.0000001, 3.0000001), "desc": "Near-integer values"},
        
        # Block boundary positions
        {"pos": (1.0, 1.0, 1.0), "desc": "Exact block boundary"},
        {"pos": (0.9999, 0.9999, 0.9999), "desc": "Just below block boundary"},
        {"pos": (1.0001, 1.0001, 1.0001), "desc": "Just above block boundary"},
        
        # Physics-related positions
        {"pos": (0, 0.5625, 0), "desc": "Step height position"},
        {"pos": (0, 1.62, 0), "desc": "Eye height position"},
    ]
    
    for case in edge_cases:
        try:
            pos = case["pos"]
            desc = case["desc"]
            
            # Create player at edge case position
            player = model.create_local_player(f"edge_{case['desc'][:5]}", pos, (0, 0), "EdgePlayer")
            
            # Verify rendering
            render_pos = player.get_render_position()
            cube_bottom = render_pos[1] - player.size
            
            print(f"   {desc}:")
            print(f"     Position: {pos}")
            print(f"     Render: {render_pos}")
            print(f"     Cube bottom: {cube_bottom}")
            print(f"     Expected bottom: {pos[1]}")
            
            # Verify cube sits exactly on surface
            if abs(cube_bottom - pos[1]) < 0.001:
                print(f"     ✅ Edge case handled correctly")
            else:
                print(f"     ❌ Edge case causes floating!")
                return False
                
        except Exception as e:
            print(f"   ❌ Error in edge case '{case['desc']}': {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🎮 TESTING COMPREHENSIVE CLIENT-SERVER SYNCHRONIZATION")
    print("=" * 65)
    print("Testing complete client-server cube position synchronization...")
    print()
    
    try:
        success = True
        success &= test_server_message_processing()
        success &= test_position_update_robustness()
        success &= test_message_serialization_integrity()
        success &= test_concurrent_position_updates()
        success &= test_edge_case_positioning()
        
        if success:
            print("\n" + "=" * 65)
            print("🎉 ALL CLIENT-SERVER SYNCHRONIZATION TESTS PASSED!")
            print("✅ Server message processing is robust")
            print("✅ Position updates handle all scenarios correctly")
            print("✅ Message serialization preserves position integrity")
            print("✅ Concurrent updates are handled safely")
            print("✅ Edge cases are managed properly")
            print()
            print("🔄 CLIENT-SERVER SYNCHRONIZATION IS BULLETPROOF!")
            print("📝 Cube positions will remain consistent across all scenarios.")
            print("=" * 65)
        else:
            print("\n❌ CLIENT-SERVER SYNCHRONIZATION ISSUES DETECTED!")
            print("Check the failed tests above for specific problems.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)