#!/usr/bin/env python3
"""
Demo script showing the cube window abstraction system.
This demonstrates how camera-type cubes can have their own pyglet windows.
"""

import time
from protocol import Cube


def demo_cube_window_system():
    """Demonstrate the cube window abstraction system."""
    print("🎬 Cube Window Abstraction System Demo")
    print("=" * 50)
    
    # Create different types of cubes
    cubes = []
    
    print("\n📦 Creating different types of cubes...")
    
    # 1. Normal cube (no window)
    normal_cube = Cube("normal_cube_1", (10, 50, 10), cube_type="normal")
    cubes.append(normal_cube)
    
    # 2. Camera cube (with window)
    camera_cube = Cube("camera_cube_1", (20, 50, 20), cube_type="camera")
    cubes.append(camera_cube)
    
    print(f"   ✅ Normal cube (window: {normal_cube.window is not None})")
    print(f"   ✅ Camera cube (window: {camera_cube.window is not None})")
    
    try:
        # Demonstrate cube functionality
        print("\n🔍 Testing cube functionality...")
        
        # Test normal cube
        print(f"\n1. Normal cube:")
        print(f"   ID: {normal_cube.id}")
        print(f"   Position: {normal_cube.position}")
        print(f"   Cube type: {normal_cube.cube_type}")
        print(f"   Has window: {normal_cube.window is not None}")
        
        # Test camera cube
        print(f"\n2. Camera cube:")
        print(f"   ID: {camera_cube.id}")
        print(f"   Position: {camera_cube.position}")
        print(f"   Cube type: {camera_cube.cube_type}")
        print(f"   Has window: {camera_cube.window is not None}")
        
        # Demonstrate child cube creation
        print(f"\n3. Creating child camera cube...")
        child_cube = camera_cube.create_child_cube('child_camera_demo', (30, 50, 30), 'camera')
        print(f"   ✅ Child camera cube created")
        print(f"   Child ID: {child_cube.id}")
        print(f"   Child type: {child_cube.cube_type}")
        print(f"   Child has window: {child_cube.window is not None}")
        
        # Test movement
        print(f"\n4. Testing cube movement...")
        original_pos = normal_cube.position
        normal_cube.update_position((15, 55, 15))
        print(f"   Normal cube moved from {original_pos} to {normal_cube.position}")
        
        # Test rotation
        print(f"\n5. Testing cube rotation...")
        original_rot = camera_cube.rotation
        camera_cube.update_rotation((45, 10))
        print(f"   Camera cube rotated from {original_rot} to {camera_cube.rotation}")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for cube in cubes:
            if cube.window:
                cube.window.close()
        print("   ✅ All cubes cleaned up")
    
    print("\n🎉 Demo completed successfully!")


def main():
    """Run the demo."""
    try:
        demo_cube_window_system()
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Cube Window Demo")
    print("💡 This demo shows how cubes can have pyglet windows for camera functionality")
    print("⚠️  Run with: DISPLAY=:99 xvfb-run -a python demo_cube_window.py")
    print()
    
    main()