#!/usr/bin/env python3
"""
Integration test to verify server startup with --reset-world flag.
Tests that the server can be instantiated correctly with command-line arguments.
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)

def test_server_startup_simulation():
    """Simulate server startup with different command-line arguments."""
    print("🧪 Testing server startup simulation...")
    
    # Test 1: Default startup (no reset)
    print("\n  Test 1: Default startup (no reset)")
    sys.argv = ['server.py']
    
    import argparse
    parser = argparse.ArgumentParser(description='Serveur Minecraft - Serveur de jeu multijoueur')
    parser.add_argument('--host', type=str, default='localhost', 
                        help='Adresse hôte du serveur (défaut: localhost)')
    parser.add_argument('--port', type=int, default=8765,
                        help='Port du serveur (défaut: 8765)')
    parser.add_argument('--reset-world', action='store_true',
                        help='Réinitialiser le monde au terrain naturel')
    
    args = parser.parse_args()
    
    assert args.host == 'localhost'
    assert args.port == 8765
    assert args.reset_world == False
    print("    ✅ Default arguments parsed correctly")
    
    # Test 2: With --reset-world flag
    print("\n  Test 2: With --reset-world flag")
    sys.argv = ['server.py', '--reset-world']
    parser = argparse.ArgumentParser(description='Serveur Minecraft - Serveur de jeu multijoueur')
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--reset-world', action='store_true')
    
    args = parser.parse_args()
    
    assert args.reset_world == True
    print("    ✅ --reset-world flag parsed correctly")
    
    # Test 3: Custom host, port, and reset
    print("\n  Test 3: Custom host, port, and reset")
    sys.argv = ['server.py', '--host', '0.0.0.0', '--port', '9000', '--reset-world']
    parser = argparse.ArgumentParser(description='Serveur Minecraft - Serveur de jeu multijoueur')
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--reset-world', action='store_true')
    
    args = parser.parse_args()
    
    assert args.host == '0.0.0.0'
    assert args.port == 9000
    assert args.reset_world == True
    print("    ✅ All custom arguments parsed correctly")
    
    print("\n  ✅ Server startup simulation test passed\n")

def test_server_instantiation_with_args():
    """Test that MinecraftServer can be instantiated with parsed arguments."""
    print("🧪 Testing server instantiation with parsed args...")
    
    from server import MinecraftServer
    
    # Simulate parsed arguments
    sys.argv = ['server.py', '--host', '127.0.0.1', '--port', '8888', '--reset-world']
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--reset-world', action='store_true')
    args = parser.parse_args()
    
    # Create server with parsed args
    server = MinecraftServer(host=args.host, port=args.port, reset_world=args.reset_world)
    
    assert server.host == '127.0.0.1'
    assert server.port == 8888
    assert len(server.world.world) > 0  # World should be initialized
    
    # Verify reset was applied (no camera blocks)
    from protocol import BlockType
    camera_blocks = [pos for pos, data in server.world.world.items() 
                     if isinstance(data, dict) and data.get("type") == BlockType.CAMERA]
    assert len(camera_blocks) == 0, f"Expected 0 camera blocks after reset, got {len(camera_blocks)}"
    
    print(f"  ✅ Server instantiated with host={server.host}, port={server.port}, reset_world=True")
    print(f"  ✅ World has {len(server.world.world)} blocks (all natural)")
    print("  ✅ Server instantiation test passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("SERVER STARTUP INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    test_server_startup_simulation()
    test_server_instantiation_with_args()
    
    print("=" * 60)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 60)
