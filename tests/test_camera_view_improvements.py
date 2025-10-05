#!/usr/bin/env python3
"""
Test to verify that camera view improvements are properly implemented.

This test validates the improvements requested:
"améliore la vision du bloc camera, en positionnant la vue plus en avant, 
un peu plus haut et plus large."

The improvements include:
1. Camera positioned more forward (moved in viewing direction)
2. Camera positioned slightly higher (increased Y offset)
3. Camera has wider field of view (increased FOV)
"""

import os
import sys
import re
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_camera_height_increased():
    """Test that camera height offset has been increased."""
    print("\n🧪 Test: Camera height offset increased")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_world_from_camera method
    render_method = content.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    
    # Check that Y offset is increased (should be > 0.6, the original value)
    y_offset_match = re.search(r'camera_y\s*\+=\s*([\d.]+)', render_method)
    assert y_offset_match, "Should find camera_y offset assignment"
    
    y_offset = float(y_offset_match.group(1))
    assert y_offset > 0.6, f"Camera height offset should be increased above 0.6, got {y_offset}"
    assert y_offset <= 1.5, f"Camera height offset should be reasonable (<=1.5), got {y_offset}"
    
    print(f"  ✓ Camera height offset increased to {y_offset} (was 0.6)")
    print("  ✓ Camera is now positioned higher for better view")
    

def test_camera_moved_forward():
    """Test that camera is positioned forward in viewing direction."""
    print("\n🧪 Test: Camera positioned forward in viewing direction")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_world_from_camera method
    render_method = content.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    
    # Check for forward movement calculation
    assert 'forward_distance' in render_method, \
        "Should calculate forward distance for camera positioning"
    assert 'forward_x' in render_method, \
        "Should calculate forward X component"
    assert 'forward_z' in render_method, \
        "Should calculate forward Z component"
    
    # Check that camera position is modified
    assert 'camera_x += forward_x' in render_method or 'camera_x = ' in render_method and 'forward_x' in render_method, \
        "Should apply forward X offset to camera position"
    assert 'camera_z += forward_z' in render_method or 'camera_z = ' in render_method and 'forward_z' in render_method, \
        "Should apply forward Z offset to camera position"
    
    # Extract forward distance value
    forward_match = re.search(r'forward_distance\s*=\s*([\d.]+)', render_method)
    if forward_match:
        forward_dist = float(forward_match.group(1))
        assert forward_dist > 0, "Forward distance should be positive"
        assert forward_dist <= 3.0, f"Forward distance should be reasonable (<=3.0), got {forward_dist}"
        print(f"  ✓ Camera moves forward by {forward_dist} blocks")
    
    print("  ✓ Camera positioned forward in viewing direction for better perspective")


def test_camera_fov_increased():
    """Test that camera field of view has been widened."""
    print("\n🧪 Test: Camera FOV increased for wider view")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_world_from_camera method
    render_method = content.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    
    # Check for FOV parameter in render_world_scene call
    fov_match = re.search(r'fov\s*=\s*([\d.]+)', render_method)
    assert fov_match, "Should find FOV parameter in render_world_scene call"
    
    fov_value = float(fov_match.group(1))
    assert fov_value > 70.0, f"FOV should be increased above 70.0, got {fov_value}"
    assert fov_value <= 110.0, f"FOV should be reasonable (<=110.0), got {fov_value}"
    
    print(f"  ✓ Camera FOV increased to {fov_value}° (was 70°)")
    print("  ✓ Camera now has wider field of view")


def test_all_improvements_together():
    """Test that all three improvements are present."""
    print("\n🧪 Test: All camera improvements implemented")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    render_method = content.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    
    improvements = []
    
    # Check for higher position
    y_offset_match = re.search(r'camera_y\s*\+=\s*([\d.]+)', render_method)
    if y_offset_match and float(y_offset_match.group(1)) > 0.6:
        improvements.append("higher position")
    
    # Check for forward movement
    if 'forward_distance' in render_method and 'forward_x' in render_method:
        improvements.append("forward positioning")
    
    # Check for wider FOV
    fov_match = re.search(r'fov\s*=\s*([\d.]+)', render_method)
    if fov_match and float(fov_match.group(1)) > 70.0:
        improvements.append("wider FOV")
    
    assert len(improvements) == 3, \
        f"All three improvements should be present, found only: {improvements}"
    
    print("  ✓ Camera positioned higher")
    print("  ✓ Camera positioned forward")
    print("  ✓ Camera has wider field of view")
    print("\n  ✅ All three improvements successfully implemented!")


if __name__ == '__main__':
    print("=" * 70)
    print("CAMERA VIEW IMPROVEMENTS TESTS")
    print("=" * 70)
    print("\nValidating improvements:")
    print("  'améliore la vision du bloc camera, en positionnant la vue")
    print("   plus en avant, un peu plus haut et plus large.'")
    print("=" * 70)
    
    try:
        test_camera_height_increased()
        print("\n✅ PASS: Camera height increased")
        
        test_camera_moved_forward()
        print("\n✅ PASS: Camera positioned forward")
        
        test_camera_fov_increased()
        print("\n✅ PASS: Camera FOV increased")
        
        test_all_improvements_together()
        print("\n✅ PASS: All improvements present")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nSummary of improvements:")
        print("  1. Camera positioned more forward (in viewing direction)")
        print("  2. Camera positioned slightly higher (increased Y offset)")
        print("  3. Camera has wider field of view (increased FOV)")
        print("\nResult: Camera blocks now have improved vision with better")
        print("        perspective, coverage and viewing angle.")
        
    except AssertionError as e:
        print(f"\n❌ FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
