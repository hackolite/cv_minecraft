#!/usr/bin/env python3
"""
Test script for the cube abstraction system
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from protocol import Cube

def test_cube_creation():
    """Test creating a cube."""
    print("🧪 Testing Cube Creation")
    print("=" * 50)
    
    # Create a cube
    cube = Cube("test_cube_1", (10, 50, 10))
    
    print(f"✅ Created cube: {cube.id}")
    print(f"   Position: {cube.position}")
    print(f"   Rotation: {cube.rotation}")
    print(f"   Size: {cube.size}")
    
    # Test position update
    cube.update_position((20, 60, 20))
    print(f"✅ Updated position: {cube.position}")
    
    # Test rotation update
    cube.update_rotation((45, 10))
    print(f"✅ Updated rotation: {cube.rotation}")
    
    print("✅ Cube creation test completed")

def test_child_cube_creation():
    """Test creating child cubes."""
    print("\n🧪 Testing Child Cube Creation")
    print("=" * 50)
    
    # Create parent cube
    parent_cube = Cube("parent_cube", (0, 50, 0))
    
    print(f"✅ Created parent cube: {parent_cube.id}")
    
    try:
        # Test child cube creation programmatically
        child_cube = parent_cube.create_child_cube("child1", (5, 50, 5))
        print(f"✅ Created child cube: {child_cube.id}")
        print(f"   Position: {child_cube.position}")
        print(f"   Parent: {child_cube.parent_cube.id}")
        
        # Create another child
        child_cube2 = parent_cube.create_child_cube("child2", (10, 50, 10))
        print(f"✅ Created second child cube: {child_cube2.id}")
        
        # List children
        print(f"✅ Parent has {len(parent_cube.child_cubes)} children: {list(parent_cube.child_cubes.keys())}")
        
        # Test destroying a child
        parent_cube.destroy_child_cube("child1")
        print(f"✅ Destroyed child1, remaining children: {list(parent_cube.child_cubes.keys())}")
                
    except Exception as e:
        print(f"❌ Child cube test failed: {e}")
    
    print("✅ Child cube creation test completed")

def test_port_management():
    """Test port allocation and release."""
    from cube_manager import cube_manager
    print("\n🧪 Testing Port Management")
    print("=" * 50)
    
    print(f"Available ports before: {cube_manager.get_available_port_count()}")
    
    # Allocate several ports
    ports = []
    for i in range(5):
        port = cube_manager.allocate_port()
        if port:
            ports.append(port)
            print(f"✅ Allocated port {port}")
        else:
            print("❌ Failed to allocate port")
    
    print(f"Available ports after allocation: {cube_manager.get_available_port_count()}")
    print(f"Used ports: {cube_manager.get_used_ports()}")
    
    # Release ports
    for port in ports:
        cube_manager.release_port(port)
        print(f"✅ Released port {port}")
    
    print(f"Available ports after release: {cube_manager.get_available_port_count()}")
    print("✅ Port management test completed")

def main():
    """Main test function."""
    print("🚀 Starting Cube System Tests")
    print("=" * 60)
    
    try:
        test_port_management()
        test_cube_creation()
        test_child_cube_creation()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()