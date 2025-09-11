#!/usr/bin/env python3
"""
Test script for the new pyCraft-inspired architecture
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol.packets import *
from protocol.connection import Connection
from protocol.auth import AuthManager
from server_new.network_server import NetworkServer
from client_new.network_client import NetworkClient


async def test_packet_serialization():
    """Test packet serialization and deserialization"""
    print("🧪 Testing packet serialization...")
    
    # Test handshake packet
    handshake = HandshakePacket(protocol_version=1, server_address="localhost", server_port=8766)
    data = handshake.to_bytes()
    
    # Parse back
    packet_id = struct.unpack('!H', data[4:6])[0]
    payload = data[6:]
    
    parsed = HandshakePacket()
    parsed.read(payload)
    
    assert parsed.protocol_version == 1
    assert parsed.server_address == "localhost"
    assert parsed.server_port == 8766
    print("✅ Handshake packet serialization works")
    
    # Test login packet
    login = LoginRequestPacket(username="TestPlayer", uuid="test-uuid-123")
    data = login.to_bytes()
    
    packet_id = struct.unpack('!H', data[4:6])[0]
    payload = data[6:]
    
    parsed = LoginRequestPacket()
    parsed.read(payload)
    
    assert parsed.username == "TestPlayer"
    assert parsed.uuid == "test-uuid-123"
    print("✅ Login packet serialization works")
    
    # Test position packet
    pos = PlayerPositionLookPacket(x=10.5, y=50.0, z=20.5, yaw=45.0, pitch=-10.0)
    data = pos.to_bytes()
    
    packet_id = struct.unpack('!H', data[4:6])[0]
    payload = data[6:]
    
    parsed = PlayerPositionLookPacket()
    parsed.read(payload)
    
    assert abs(parsed.x - 10.5) < 0.001
    assert abs(parsed.y - 50.0) < 0.001
    assert abs(parsed.z - 20.5) < 0.001
    assert abs(parsed.yaw - 45.0) < 0.001
    assert abs(parsed.pitch - (-10.0)) < 0.001
    print("✅ Position packet serialization works")


async def test_auth_manager():
    """Test authentication manager"""
    print("🧪 Testing authentication manager...")
    
    auth = AuthManager(online_mode=False)
    
    # Test offline authentication
    success, message, session = auth.authenticate_player("TestPlayer")
    assert success
    assert session is not None
    assert session.username == "TestPlayer"
    assert session.authenticated
    print("✅ Offline authentication works")
    
    # Test session management
    retrieved = auth.get_session(session.uuid)
    assert retrieved is not None
    assert retrieved.username == "TestPlayer"
    print("✅ Session management works")
    
    # Test duplicate username
    success2, message2, session2 = auth.authenticate_player("TestPlayer")
    assert success2
    assert session2.uuid == session.uuid  # Should reuse session
    print("✅ Session reuse works")


async def test_world_manager():
    """Test world manager"""
    print("🧪 Testing world manager...")
    
    from server_new.world_manager import WorldManager
    
    world = WorldManager()
    
    # Test block operations
    pos = (10, 50, 20)
    assert not world.has_block(pos)
    
    world.set_block(pos, "GRASS")
    assert world.has_block(pos)
    
    block = world.get_block(pos)
    assert block is not None
    assert block.block_type == "GRASS"
    
    world.remove_block(pos)
    assert not world.has_block(pos)
    print("✅ World block operations work")
    
    # Test small world generation
    await world.generate_world(size=8)  # Small world for testing
    assert world.get_block_count() > 0
    print(f"✅ World generation works ({world.get_block_count()} blocks)")


async def test_player_manager():
    """Test player manager"""
    print("🧪 Testing player manager...")
    
    from server_new.player_manager import PlayerManager
    
    pm = PlayerManager()
    
    # Test player creation
    player = await pm.create_player("test-uuid", "TestPlayer")
    assert player.username == "TestPlayer"
    assert player.uuid == "test-uuid"
    print("✅ Player creation works")
    
    # Test player retrieval
    retrieved = pm.get_player("test-uuid")
    assert retrieved is not None
    assert retrieved.username == "TestPlayer"
    
    by_username = pm.get_player_by_username("TestPlayer")
    assert by_username is not None
    assert by_username.uuid == "test-uuid"
    print("✅ Player retrieval works")
    
    # Test position update
    await pm.update_player_position("test-uuid", [100.0, 60.0, 200.0], [90.0, -45.0])
    assert player.position == [100.0, 60.0, 200.0]
    assert player.rotation == [90.0, -45.0]
    print("✅ Player position updates work")


async def test_network_protocol():
    """Test basic network protocol"""
    print("🧪 Testing network protocol...")
    
    # This would require actually starting server and client
    # For now, just test that we can create the components
    
    try:
        # Test that we can create network client
        client = NetworkClient("TestPlayer")
        assert client.username == "TestPlayer"
        print("✅ Network client creation works")
        
        # Test that we can create network server
        server = NetworkServer("localhost", 9999)  # Use different port
        assert server.host == "localhost"
        assert server.port == 9999
        print("✅ Network server creation works")
        
    except Exception as e:
        print(f"❌ Network protocol test failed: {e}")
        raise


async def run_all_tests():
    """Run all tests"""
    print("🚀 Running pyCraft-inspired architecture tests")
    print("=" * 50)
    
    try:
        await test_packet_serialization()
        print()
        
        await test_auth_manager()
        print()
        
        await test_world_manager()
        print()
        
        await test_player_manager()
        print()
        
        await test_network_protocol()
        print()
        
        print("🎉 All tests passed!")
        print("✅ pyCraft-inspired architecture is working correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def main():
    """Main test entry point"""
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    success = await run_all_tests()
    
    if success:
        print("\n🎮 Architecture ready for use!")
        print("• Start server: python3 server_new_main.py")
        print("• Start client: python3 client_new_main.py [username]")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())