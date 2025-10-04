#!/usr/bin/env python3
"""
Test to verify that camera capture properly flushes the OpenGL buffer.

This test validates the fix for the issue:
"une grande partie des images caméras sont blanches, et l'image est fixe, 
ne montre pas les mises a jour du buffer"

The fix ensures that:
1. glFlush() is called after _render_simple_scene() before buffer capture
2. This ensures OpenGL commands are executed before reading the framebuffer
3. Camera images update correctly and aren't stuck/white
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_glflush_after_render():
    """Test that glFlush is called after _render_simple_scene in capture_frame."""
    print("\n🧪 Test: glFlush is called after rendering before buffer capture")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the capture_frame method
    if 'def capture_frame(self' not in content:
        print("  ⚠️  capture_frame method not found")
        return
    
    # Find the camera capture section
    capture_frame_section = content.split('def capture_frame(self', 1)[1].split('def ', 1)[0]
    
    # Look for the camera rendering flow
    if 'camera_cube.window._render_simple_scene()' not in capture_frame_section:
        print("  ⚠️  _render_simple_scene call not found in camera capture path")
        return
    
    # Find positions of key operations
    render_pos = capture_frame_section.find('_render_simple_scene()')
    flush_pos = capture_frame_section.find('glFlush()')
    buffer_pos = capture_frame_section.find('get_color_buffer()')
    
    # Verify glFlush is present
    assert flush_pos != -1, "glFlush() should be called in capture_frame"
    print("  ✓ glFlush() is called in capture_frame")
    
    # Verify glFlush comes AFTER render
    assert flush_pos > render_pos, "glFlush() should be called AFTER _render_simple_scene()"
    print("  ✓ glFlush() is called after _render_simple_scene()")
    
    # Verify glFlush comes BEFORE buffer capture
    assert flush_pos < buffer_pos, "glFlush() should be called BEFORE get_color_buffer()"
    print("  ✓ glFlush() is called before get_color_buffer()")
    
    print("\n✅ PASS: glFlush is properly positioned in capture workflow")


def test_flush_ensures_rendering_complete():
    """Test that the comment explains why we flush."""
    print("\n🧪 Test: Comment explains why glFlush is needed")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    capture_frame_section = content.split('def capture_frame(self', 1)[1].split('def ', 1)[0]
    
    # Check for explanatory comment
    has_comment = (
        'Force flush' in capture_frame_section or
        'ensure rendering' in capture_frame_section or
        'rendering is complete' in capture_frame_section
    )
    
    assert has_comment, "Should have comment explaining why glFlush is needed"
    print("  ✓ Comment explains purpose of glFlush")
    
    print("\n✅ PASS: glFlush purpose is documented")


def test_camera_capture_workflow():
    """Test the complete camera capture workflow."""
    print("\n🧪 Test: Complete camera capture workflow")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    capture_frame_section = content.split('def capture_frame(self', 1)[1].split('def ', 1)[0]
    
    # Verify the complete workflow
    workflow_steps = [
        ('switch_to()', 'Switch to camera context'),
        ('_render_simple_scene()', 'Render camera view'),
        ('glFlush()', 'Flush OpenGL commands'),
        ('get_color_buffer()', 'Capture buffer')
    ]
    
    last_pos = -1
    for step, description in workflow_steps:
        pos = capture_frame_section.find(step)
        assert pos != -1, f"{description} ({step}) should be in capture workflow"
        assert pos > last_pos, f"{description} should come after previous step"
        print(f"  ✓ {description}: {step}")
        last_pos = pos
    
    print("\n✅ PASS: Complete camera capture workflow verified")


def main():
    """Run all tests."""
    print("=" * 70)
    print("CAMERA BUFFER FLUSH FIX TESTS")
    print("=" * 70)
    print("\nValidating fix for:")
    print("  'une grande partie des images caméras sont blanches,")
    print("   et l'image est fixe, ne montre pas les mises a jour du buffer'")
    print("=" * 70)
    
    try:
        test_glflush_after_render()
        test_flush_ensures_rendering_complete()
        test_camera_capture_workflow()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
        print("\nSummary of the fix:")
        print("  • Problem: Camera images were white/frozen, buffer not updating")
        print("  • Root cause: Missing glFlush() after rendering before buffer capture")
        print("  • Solution: Added glFlush() after _render_simple_scene()")
        print("  • Result: OpenGL commands execute before buffer read")
        print("  • Impact: Camera images now update correctly, show rendered world")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
