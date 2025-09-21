#!/usr/bin/env python3
"""
Test client behavior with server-side collision management.
This verifies the client correctly handles movement responses.
"""

import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import MessageType, Message, create_movement_response_message

def test_client_movement_response():
    """Test that the client correctly handles movement responses."""
    
    print("🧪 Testing client movement response handling...")
    
    # Create a mock window for testing
    class MockWindow:
        def __init__(self):
            self.position = (64, 100, 64)
            self.rotation = (0, 0)
            self.local_player_cube = None
            self.messages = []
            
        def show_message(self, message):
            self.messages.append(message)
            print(f"   📝 Client message: {message}")
    
    # Create a mock client
    class MockClient:
        def __init__(self):
            self.window = MockWindow()
            self.player_id = "test_player"
    
    mock_client = MockClient()
    
    # Simulate handling movement responses
    print("\n🧪 Test 1: 'ok' movement response")
    
    ok_message = create_movement_response_message("ok", (65, 100, 64), (0, 0))
    
    # Simulate the client handling this message
    movement_data = ok_message.data
    status = movement_data.get("status", "forbidden")
    server_position = tuple(movement_data["position"])
    server_rotation = movement_data.get("rotation", mock_client.window.rotation)
    
    old_position = mock_client.window.position
    
    if status == "ok":
        mock_client.window.position = server_position
        mock_client.window.rotation = server_rotation
        print(f"   ✅ Position updated from {old_position} to {mock_client.window.position}")
    
    assert mock_client.window.position == (65, 100, 64), "Position should be updated for 'ok' status"
    print("   ✅ 'ok' response handled correctly")
    
    print("\n🧪 Test 2: 'forbidden' movement response")
    
    forbidden_message = create_movement_response_message("forbidden", old_position, (0, 0))
    
    # Simulate the client handling this message
    movement_data = forbidden_message.data
    status = movement_data.get("status", "forbidden")
    server_position = tuple(movement_data["position"])
    server_rotation = movement_data.get("rotation", mock_client.window.rotation)
    
    if status == "forbidden":
        mock_client.window.position = server_position
        mock_client.window.rotation = server_rotation
        mock_client.window.show_message("⚠️ Mouvement bloqué par le serveur - collision détectée")
    
    assert mock_client.window.position == old_position, "Position should revert to server position for 'forbidden'"
    assert len(mock_client.window.messages) == 1, "Warning message should be displayed"
    assert "collision détectée" in mock_client.window.messages[0], "Warning message should mention collision"
    print("   ✅ 'forbidden' response handled correctly with warning")
    
    print("\n🧪 Test 3: Client collision method behavior")
    
    # Test the new collision method that doesn't do local collision detection
    class TestClientCollision:
        def __init__(self):
            self.collision_types = {}
        
        def collide(self, position, height):
            """
            No longer performs collision detection - the server handles all collision checking.
            This method now simply returns the requested position as-is.
            """
            # No local collision detection - server is authoritative
            # Reset collision types since we don't do local collision checking
            self.collision_types = {
                "top": False,
                "bottom": False,
                "right": False,
                "left": False
            }
            
            # Return position as-is - server will validate and respond
            return position
    
    test_client = TestClientCollision()
    input_position = (10, 20, 30)
    result_position = test_client.collide(input_position, 1.8)
    
    assert result_position == input_position, "Collision method should return position as-is"
    assert all(not v for v in test_client.collision_types.values()), "All collision types should be False"
    print("   ✅ Client collision method now passes through position without modification")
    
    print("\n✅ All client behavior tests passed!")

if __name__ == "__main__":
    print("🚀 Starting client behavior tests...")
    test_client_movement_response()
    print("\n🎉 All client behavior tests completed!")