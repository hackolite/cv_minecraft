#!/usr/bin/env python3
"""
Simple test client for the new pyCraft-inspired server
Tests the network protocol without requiring display
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client_new.network_client import NetworkClient


class TestClient:
    """Simple test client for validation"""
    
    def __init__(self, username: str):
        self.username = username
        self.network_client = NetworkClient(username)
        self.connected = False
        self.world_blocks_received = 0
        
        # Setup callbacks
        self.network_client.on_login_success = self._on_login_success
        self.network_client.on_world_update = self._on_world_update
        self.network_client.on_block_change = self._on_block_change
        self.network_client.on_chat_message = self._on_chat_message
        self.network_client.on_disconnect = self._on_disconnect
    
    async def _on_login_success(self, username: str, uuid: str, spawn_pos: list):
        """Handle successful login"""
        print(f"✅ Login successful as {username} (UUID: {uuid})")
        print(f"📍 Spawn position: {spawn_pos}")
        self.connected = True
    
    async def _on_world_update(self, blocks: list):
        """Handle world update"""
        self.world_blocks_received += len(blocks)
        print(f"🌍 Received {len(blocks)} blocks (total: {self.world_blocks_received})")
    
    async def _on_block_change(self, x: int, y: int, z: int, block_type: str, action: str):
        """Handle block change"""
        print(f"🧱 Block {action}: {block_type} at ({x}, {y}, {z})")
    
    async def _on_chat_message(self, sender: str, message: str, timestamp: float):
        """Handle chat message"""
        print(f"💬 [{sender}]: {message}")
    
    async def _on_disconnect(self, reason: str):
        """Handle disconnect"""
        print(f"❌ Disconnected: {reason}")
        self.connected = False
    
    async def test_connection(self, host: str = "localhost", port: int = 8766):
        """Test connection to server"""
        print(f"🔌 Connecting to {host}:{port} as {self.username}...")
        
        try:
            # Connect to server
            success = await self.network_client.connect(host, port)
            
            if not success:
                print("❌ Failed to connect to server")
                return False
            
            # Wait a bit for login process
            await asyncio.sleep(2)
            
            if not self.connected:
                print("❌ Login process failed")
                return False
            
            # Test position update
            print("📍 Sending position update...")
            await self.network_client.send_position_update(35.0, 55.0, 85.0, 45.0, -10.0)
            
            # Test chat message
            print("💬 Sending chat message...")
            await self.network_client.send_chat_message("Hello from test client!")
            
            # Test block placement
            print("🧱 Testing block placement...")
            await self.network_client.send_block_change(36, 55, 86, "BRICK", "place")
            
            # Wait a bit for responses
            await asyncio.sleep(2)
            
            # Test block removal
            print("🧱 Testing block removal...")
            await self.network_client.send_block_change(36, 55, 86, "", "remove")
            
            # Wait a bit more
            await asyncio.sleep(2)
            
            print("✅ All tests completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Disconnect
            if self.network_client.is_connected():
                await self.network_client.disconnect("Test completed")


async def main():
    """Main test entry point"""
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    # Get username from command line
    username = sys.argv[1] if len(sys.argv) > 1 else "TestClient"
    
    print(f"🧪 Testing pyCraft-inspired protocol with client '{username}'")
    print("=" * 60)
    
    # Create test client
    test_client = TestClient(username)
    
    # Run test
    success = await test_client.test_connection()
    
    if success:
        print("\n🎉 Protocol test successful!")
        print("✅ The new pyCraft-inspired architecture is working correctly")
        print(f"🌍 Received {test_client.world_blocks_received} blocks from server")
    else:
        print("\n❌ Protocol test failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        sys.exit(1)