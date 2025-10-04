#!/usr/bin/env python3
"""
Demo: Camera Cube World Rendering

This demo shows how camera cubes can now render the actual world from their 
perspective instead of just showing a simple placeholder cube.

Before this fix:
  - Camera cubes rendered a simple colored cube placeholder
  - Recordings from cameras showed only the placeholder

After this fix:
  - Camera cubes render the actual world from their position/rotation
  - Recordings capture the real world as seen from the camera's perspective
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol import Cube, BlockType
from minecraft_client_fr import EnhancedClientModel


def demo_camera_world_rendering():
    """Demonstrate camera cube world rendering."""
    print("=" * 70)
    print("CAMERA CUBE WORLD RENDERING DEMO")
    print("=" * 70)
    print()
    print("This demo shows how camera cubes now render the actual world")
    print("from their perspective, instead of just a placeholder cube.")
    print()
    
    # Step 1: Create a world model
    print("Step 1: Creating world model with blocks")
    print("-" * 70)
    model = EnhancedClientModel()
    
    # Add various blocks to create an interesting scene
    scene_blocks = [
        # Ground level
        ((10, 50, 10), BlockType.GRASS),
        ((11, 50, 10), BlockType.GRASS),
        ((12, 50, 10), BlockType.GRASS),
        ((10, 50, 11), BlockType.GRASS),
        ((11, 50, 11), BlockType.GRASS),
        ((12, 50, 11), BlockType.GRASS),
        
        # A simple structure
        ((11, 51, 10), BlockType.BRICK),
        ((11, 52, 10), BlockType.BRICK),
        ((11, 53, 10), BlockType.WOOD),
        
        # Some decorative blocks
        ((13, 50, 10), BlockType.SAND),
        ((14, 50, 10), BlockType.STONE),
    ]
    
    for pos, block_type in scene_blocks:
        model.add_block(pos, block_type, immediate=True)
    
    print(f"✅ Created world with {len(model.world)} blocks")
    print(f"   Blocks include: GRASS, BRICK, WOOD, SAND, STONE")
    print()
    
    # Step 2: Create camera WITHOUT model (old behavior)
    print("Step 2: Creating camera WITHOUT model (old behavior)")
    print("-" * 70)
    camera_old = Cube(
        cube_id="camera_placeholder",
        position=(15, 52, 15),
        rotation=(0, 0),
        cube_type="camera"
        # No model parameter - will use placeholder rendering
    )
    
    if camera_old.window:
        print(f"✅ Camera created: {camera_old.id}")
        print(f"   Position: {camera_old.position}")
        print(f"   Rotation: {camera_old.rotation}")
        print(f"   Has model: {camera_old.window.model is not None}")
        print(f"   Rendering mode: PLACEHOLDER (colored cube)")
        print()
    
    # Step 3: Create camera WITH model (new behavior)
    print("Step 3: Creating camera WITH model (new behavior)")
    print("-" * 70)
    camera_new = Cube(
        cube_id="camera_world_view",
        position=(15, 52, 15),
        rotation=(225, 10),  # Looking towards the structure
        cube_type="camera",
        model=model  # Provide model for world rendering
    )
    
    if camera_new.window:
        print(f"✅ Camera created: {camera_new.id}")
        print(f"   Position: {camera_new.position}")
        print(f"   Rotation: {camera_new.rotation}")
        print(f"   Has model: {camera_new.window.model is not None}")
        print(f"   Rendering mode: WORLD VIEW (actual scene)")
        print()
    
    # Step 4: Demonstrate the difference
    print("Step 4: Key Differences")
    print("-" * 70)
    print()
    print("📷 Camera WITHOUT model (camera_placeholder):")
    print("   • Renders a simple colored cube as placeholder")
    print("   • Used on server side where world rendering is not needed")
    print("   • Lightweight and fast")
    print()
    print("🌍 Camera WITH model (camera_world_view):")
    print("   • Renders the actual world from camera's position/rotation")
    print("   • Shows all blocks visible from the camera's perspective")
    print("   • Uses the same rendering pipeline as the main player view")
    print("   • Perfect for recording gameplay from camera's viewpoint")
    print()
    
    # Step 5: Recording use case
    print("Step 5: Recording Use Case")
    print("-" * 70)
    print()
    print("When recording gameplay from a camera:")
    print()
    print("BEFORE this fix:")
    print("  self.camera_cube.window._render_simple_scene()")
    print("  ↓")
    print("  Rendered placeholder cube (not useful)")
    print()
    print("AFTER this fix:")
    print("  self.camera_cube.window._render_simple_scene()")
    print("  ↓")
    print("  if model and cube:")
    print("    _render_world_from_camera()  # Actual world view!")
    print("  else:")
    print("    _render_placeholder_cube()   # Fallback")
    print()
    
    # Cleanup
    print("Step 6: Cleanup")
    print("-" * 70)
    if camera_old.window:
        camera_old.window.close()
    if camera_new.window:
        camera_new.window.close()
    print("✅ Cameras cleaned up")
    print()
    
    # Summary
    print("=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print("  • Camera cubes can now render the actual world")
    print("  • Recordings show real gameplay from camera's perspective")
    print("  • Backward compatible - works without model parameter")
    print("  • Automatic fallback to placeholder when needed")
    print()


def main():
    """Run the demo."""
    try:
        demo_camera_world_rendering()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    print()
    print("🎬 Starting Camera World Rendering Demo")
    print()
    sys.exit(main())
