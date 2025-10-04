#!/usr/bin/env python3
"""
Demo: Factorized Rendering Pipeline

This demo demonstrates how the factorized rendering pipeline works:
1. Camera cubes automatically create headless windows
2. Both main window and camera cubes use the same rendering function
3. Recordings from cameras save to correct folder structure
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol import Cube, render_world_scene


def main():
    print("=" * 70)
    print("FACTORIZED RENDERING PIPELINE DEMO")
    print("=" * 70)
    print()
    
    # Demo 1: Create camera cubes
    print("Demo 1: Creating Camera Cubes")
    print("-" * 70)
    print()
    
    cameras = []
    for i in range(3):
        camera = Cube(
            cube_id=f"camera_{i}",
            position=(10 * i, 50, 10 * i),
            rotation=(45 * i, 10),
            cube_type="camera",
            owner="demo_player"
        )
        cameras.append(camera)
        print(f"✅ Created camera_{i}:")
        print(f"   - Position: {camera.position}")
        print(f"   - Rotation: {camera.rotation}")
        print(f"   - Has window: {camera.window is not None}")
        print(f"   - Window visible: {camera.window.visible if camera.window else 'N/A'}")
        print()
    
    # Demo 2: Show render_world_scene function
    print("Demo 2: Shared Rendering Function")
    print("-" * 70)
    print()
    print("Function signature:")
    print("  render_world_scene(")
    print("    model,                        # World model")
    print("    position,                     # Camera position (x, y, z)")
    print("    rotation,                     # Camera rotation (h, v)")
    print("    window_size,                  # Window size (w, h)")
    print("    fov=70.0,                     # Field of view")
    print("    render_players_func=None,     # Optional player rendering")
    print("    render_focused_block_func=None, # Optional focused block")
    print("    setup_perspective_func=None   # Optional custom perspective")
    print("  )")
    print()
    print("✅ This function is used by:")
    print("   - Camera cubes (headless rendering)")
    print("   - Can be used by main window (optional)")
    print()
    
    # Demo 3: Recording structure
    print("Demo 3: Recording Folder Structure")
    print("-" * 70)
    print()
    print("When F1/F2/F3 are pressed, recordings are saved to:")
    print()
    for i, camera in enumerate(cameras):
        print(f"  F{i+1} (Camera {i}):")
        print(f"    recordings/{camera.id}/")
        print(f"    └── session_20231004_143025/")
        print(f"        ├── frame_000001.jpg")
        print(f"        ├── frame_000002.jpg")
        print(f"        └── session_info.json")
        print()
    
    # Demo 4: How it works
    print("Demo 4: How Rendering Works")
    print("-" * 70)
    print()
    print("Step 1: Camera cube is created")
    print("  → Cube(cube_type='camera', model=world_model)")
    print()
    print("Step 2: Window is created automatically")
    print("  → CubeWindow(..., visible=False, model=model, cube=self)")
    print()
    print("Step 3: When recording, frame is captured")
    print("  → window._render_simple_scene()")
    print()
    print("Step 4: Scene is rendered using shared function")
    print("  → render_world_scene(model, position, rotation, size)")
    print()
    print("Step 5: Both main window and cameras use same logic")
    print("  → Ensures consistency across all views")
    print()
    
    # Demo 5: Benefits
    print("Demo 5: Benefits of Factorization")
    print("-" * 70)
    print()
    print("✅ Code Reuse:")
    print("   Single function used by all views")
    print()
    print("✅ Consistency:")
    print("   Identical rendering across main window and cameras")
    print()
    print("✅ Maintainability:")
    print("   Changes only need to be made once")
    print()
    print("✅ Flexibility:")
    print("   Optional callbacks for customization")
    print()
    print("✅ Testing:")
    print("   Easy to verify both paths use same logic")
    print()
    
    # Cleanup
    print("Cleanup")
    print("-" * 70)
    for camera in cameras:
        if camera.window:
            camera.window.close()
    print(f"✅ Closed {len(cameras)} camera windows")
    print()
    
    # Summary
    print("=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print("  • Camera cubes automatically create headless windows")
    print("  • Both main window and cameras use render_world_scene()")
    print("  • Recordings save to recordings/camera_X/session_TIMESTAMP/")
    print("  • Factorized rendering ensures consistency")
    print()


if __name__ == "__main__":
    main()
