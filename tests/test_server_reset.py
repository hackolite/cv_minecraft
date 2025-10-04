#!/usr/bin/env python3
"""
Test that server can be instantiated with reset_world parameter.
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)

from server import MinecraftServer
from protocol import BlockType

def test_server_initialization_with_reset():
    """Test that MinecraftServer can be created with reset_world=True."""
    print("🧪 Testing MinecraftServer initialization with reset_world...")
    
    # Create server with reset_world=True
    server = MinecraftServer(host='localhost', port=8765, reset_world=True)
    
    # Verify world exists
    assert server.world is not None
    print(f"  Server world created with {len(server.world.world)} blocks")
    
    # Verify no camera blocks exist
    camera_blocks = [pos for pos, data in server.world.world.items() 
                     if isinstance(data, dict) and data.get("type") == BlockType.CAMERA]
    assert len(camera_blocks) == 0, f"Expected 0 camera blocks, got {len(camera_blocks)}"
    print("  ✅ No camera blocks found (expected)")
    
    # Verify only natural blocks
    non_natural_blocks = []
    natural_types = {BlockType.GRASS, BlockType.SAND, BlockType.STONE, 
                     BlockType.WATER, BlockType.WOOD, BlockType.LEAF}
    
    for pos, block_data in server.world.world.items():
        if isinstance(block_data, dict):
            block_type = block_data.get("type")
        else:
            block_type = block_data
        
        if block_type not in natural_types:
            non_natural_blocks.append((pos, block_type))
    
    assert len(non_natural_blocks) == 0, f"Found {len(non_natural_blocks)} non-natural blocks"
    print("  ✅ Only natural blocks found (expected)")
    
    print("  ✅ Server initialization with reset_world test passed\n")

def test_server_initialization_without_reset():
    """Test that MinecraftServer works normally without reset_world."""
    print("🧪 Testing MinecraftServer initialization without reset_world...")
    
    # Create server with reset_world=False (default)
    server = MinecraftServer(host='localhost', port=8765, reset_world=False)
    
    # Verify camera blocks exist
    camera_blocks = [pos for pos, data in server.world.world.items() 
                     if isinstance(data, dict) and data.get("type") == BlockType.CAMERA]
    assert len(camera_blocks) == 5, f"Expected 5 camera blocks, got {len(camera_blocks)}"
    print(f"  ✅ Found {len(camera_blocks)} camera blocks (expected)")
    
    print("  ✅ Server initialization without reset_world test passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("SERVER INITIALIZATION TESTS")
    print("=" * 60 + "\n")
    
    test_server_initialization_with_reset()
    test_server_initialization_without_reset()
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
