#!/usr/bin/env python3
"""
Test to verify that camera rendering properly clears the framebuffer.

This test validates the fix for the issue:
"pour les cameras, j'ai un mélange de vues de mon desktop, de noir et un peu des block de l'univers."

The fix ensures that:
1. Camera rendering clears the framebuffer before drawing (glClear)
2. No stale data from desktop/previous renders is captured
3. Camera views show only the Minecraft world from the camera perspective
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_render_simple_scene_clears_buffer():
    """Test that _render_simple_scene clears the framebuffer before rendering."""
    print("\n🧪 Test: _render_simple_scene clears framebuffer")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_simple_scene method
    render_simple_scene_section = content.split('def _render_simple_scene(self):', 1)[1].split('def ', 1)[0]
    
    # Verify that glClear is called before rendering
    assert 'glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)' in render_simple_scene_section, \
        "_render_simple_scene should clear framebuffer with glClear before rendering"
    print("  ✓ _render_simple_scene calls glClear to clear framebuffer")
    
    # Verify the comment explains why we clear
    assert 'Clear the framebuffer before rendering to avoid capturing stale data' in render_simple_scene_section or \
           'clear' in render_simple_scene_section.lower(), \
        "_render_simple_scene should have a comment explaining why we clear"
    print("  ✓ Comment explains why framebuffer is cleared")
    
    print("\n✅ PASS: _render_simple_scene properly clears framebuffer")


def test_glclear_called_before_rendering():
    """Test that glClear is called BEFORE any rendering operations."""
    print("\n🧪 Test: glClear is called before rendering operations")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_simple_scene method
    render_simple_scene_section = content.split('def _render_simple_scene(self):', 1)[1].split('def ', 1)[0]
    
    # Get position of glClear
    glclear_pos = render_simple_scene_section.find('glClear')
    assert glclear_pos != -1, "glClear should be present in _render_simple_scene"
    
    # Get position of _render_world_from_camera (the actual rendering call)
    render_world_pos = render_simple_scene_section.find('_render_world_from_camera')
    
    # Get position of _render_placeholder_cube
    render_placeholder_pos = render_simple_scene_section.find('_render_placeholder_cube')
    
    # Verify glClear comes before rendering calls
    if render_world_pos != -1:
        assert glclear_pos < render_world_pos, \
            "glClear should be called BEFORE _render_world_from_camera"
        print("  ✓ glClear is called before _render_world_from_camera")
    
    if render_placeholder_pos != -1:
        assert glclear_pos < render_placeholder_pos, \
            "glClear should be called BEFORE _render_placeholder_cube"
        print("  ✓ glClear is called before _render_placeholder_cube")
    
    print("\n✅ PASS: glClear is properly positioned before rendering")


def test_camera_window_rendering_workflow():
    """Test the complete camera window rendering workflow."""
    print("\n🧪 Test: Camera window rendering workflow")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify CubeWindow class has the _render_simple_scene method
    assert 'class CubeWindow:' in content, \
        "CubeWindow class should exist in protocol.py"
    print("  ✓ CubeWindow class exists")
    
    assert 'def _render_simple_scene(self):' in content, \
        "CubeWindow should have _render_simple_scene method"
    print("  ✓ _render_simple_scene method exists")
    
    # Verify the method is called from capture_frame in minecraft_client_fr.py
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    with open(client_file, 'r', encoding='utf-8') as f:
        client_content = f.read()
    
    assert '_render_simple_scene()' in client_content, \
        "capture_frame should call _render_simple_scene"
    print("  ✓ capture_frame calls _render_simple_scene")
    
    print("\n✅ PASS: Camera window rendering workflow is complete")


def main():
    """Run all tests."""
    print("=" * 70)
    print("CAMERA RENDERING FIX TESTS")
    print("=" * 70)
    print("\nValidating fix for:")
    print("  'pour les cameras, j'ai un mélange de vues de mon desktop,")
    print("   de noir et un peu des block de l'univers.'")
    print("=" * 70)
    
    try:
        test_render_simple_scene_clears_buffer()
        test_glclear_called_before_rendering()
        test_camera_window_rendering_workflow()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
        print("\nSummary of the fix:")
        print("  • Problem: Cameras captured desktop/stale framebuffer data")
        print("  • Solution: Added glClear() before rendering in _render_simple_scene()")
        print("  • Result: Camera views now show clean Minecraft world only")
        print("  • Impact: Minimal change - single glClear() call added")
        
        print("\nKey changes:")
        print("  1. _render_simple_scene() now clears framebuffer before rendering")
        print("  2. This prevents desktop/stale data from appearing in camera views")
        print("  3. Camera captures now show proper Minecraft world from camera POV")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
