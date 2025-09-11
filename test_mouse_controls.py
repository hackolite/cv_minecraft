#!/usr/bin/env python3
"""
Test mouse controls for view changes
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mouse_controls_implementation():
    """Test that mouse controls are properly implemented"""
    print("🧪 Testing mouse controls implementation...")
    
    try:
        from client import DebugClient
        
        # Check that disableMouse is not called
        import inspect
        source = inspect.getsource(DebugClient.setup_camera)
        
        if "disableMouse" in source:
            print("❌ disableMouse() is still being called - mouse controls disabled")
            return False
        else:
            print("✅ disableMouse() is not called - mouse controls should work")
        
        # Check for mouse handling method
        if hasattr(DebugClient, 'handle_mouse_movement'):
            print("✅ handle_mouse_movement method found")
        else:
            print("❌ handle_mouse_movement method not found")
            return False
        
        # Check for mouse sensitivity and camera variables
        source_init = inspect.getsource(DebugClient.setup_camera)
        if "mouse_sensitivity" in source_init:
            print("✅ Mouse sensitivity variable found")
        else:
            print("❌ Mouse sensitivity variable not found")
            return False
        
        if "camera_pitch" in source_init and "camera_yaw" in source_init:
            print("✅ Camera pitch and yaw variables found")
        else:
            print("❌ Camera pitch/yaw variables not found")
            return False
        
        # Check for mouse click handlers
        if hasattr(DebugClient, 'mouse_click') and hasattr(DebugClient, 'mouse_right_click'):
            print("✅ Mouse click handlers found")
        else:
            print("❌ Mouse click handlers not found")
            return False
        
        # Check update method includes mouse handling
        source_update = inspect.getsource(DebugClient.update)
        if "handle_mouse_movement" in source_update:
            print("✅ Mouse handling integrated in update loop")
        else:
            print("❌ Mouse handling not integrated in update loop")
            return False
        
        print("✅ All mouse control components are properly implemented")
        return True
        
    except Exception as e:
        print(f"❌ Error testing mouse controls: {e}")
        return False

def test_block_reduction():
    """Test that block generation has been reduced"""
    print("🧪 Testing block reduction...")
    
    try:
        from server import MinecraftServer
        
        # Test default server
        default_server = MinecraftServer()
        default_blocks = len(default_server)
        
        # Test old size for comparison
        old_server = MinecraftServer(world_size=64)
        old_blocks = len(old_server)
        
        print(f"✅ Default server (size {default_server.world.world_size}): {default_blocks} blocks")
        print(f"✅ Old size server (size 64): {old_blocks} blocks")
        
        reduction_percent = ((old_blocks - default_blocks) / old_blocks) * 100
        print(f"✅ Block reduction: {reduction_percent:.1f}%")
        
        if default_blocks < old_blocks:
            print("✅ Block count successfully reduced")
            return True
        else:
            print("❌ Block count not reduced")
            return False
            
    except Exception as e:
        print(f"❌ Error testing block reduction: {e}")
        return False

def main():
    """Main test function"""
    print("🎮 Testing Mouse Controls and Block Reduction")
    print("=" * 50)
    
    # Test 1: Mouse controls implementation
    mouse_ok = test_mouse_controls_implementation()
    print()
    
    # Test 2: Block reduction
    blocks_ok = test_block_reduction()
    print()
    
    if mouse_ok and blocks_ok:
        print("✅ All tests passed!")
        print("🎮 Features implemented:")
        print("   • Mouse controls for view changes")
        print("   • Reduced block generation for better performance")
        print("   • Keyboard controls still available as fallback")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)