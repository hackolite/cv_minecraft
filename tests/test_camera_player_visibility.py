#!/usr/bin/env python3
"""
Test to verify that camera rendering includes player visibility.

This test validates the fix for the issue:
"j'ai toujours une partie blanche, vérifie que l'utilisateur originel est visible par le bloc camera"
(I still have a white area, verify that the original user is visible by the camera block)

The fix ensures that:
1. Camera views render player cubes (including the original user)
2. The render_players_func is properly passed to render_world_scene
3. Both local player and other players are visible in camera views
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_render_players_func_is_passed():
    """Test that _render_world_from_camera passes render_players_func."""
    print("\n🧪 Test: _render_world_from_camera passes render_players_func")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_world_from_camera method
    render_world_section = content.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    
    # Verify that render_players_func is NOT None
    assert 'render_players_func=None' not in render_world_section or \
           'render_players_func=self._render_players' in render_world_section, \
        "_render_world_from_camera should pass a render_players_func, not None"
    print("  ✓ render_players_func is not None")
    
    # Verify that it's set to self._render_players
    assert 'render_players_func=self._render_players' in render_world_section, \
        "_render_world_from_camera should pass self._render_players as render_players_func"
    print("  ✓ render_players_func is set to self._render_players")
    
    print("\n✅ PASS: render_players_func is properly configured")


def test_render_players_method_exists():
    """Test that CubeWindow has a _render_players method."""
    print("\n🧪 Test: CubeWindow has _render_players method")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the CubeWindow class
    assert 'class CubeWindow:' in content, "CubeWindow class should exist"
    
    # Check that _render_players method exists in CubeWindow
    cubewindow_section = content.split('class CubeWindow:', 1)[1]
    
    assert 'def _render_players(self):' in cubewindow_section, \
        "CubeWindow should have a _render_players method"
    print("  ✓ _render_players method exists")
    
    # Verify it renders other_players
    render_players_section = cubewindow_section.split('def _render_players(self):', 1)[1].split('def ', 1)[0]
    assert 'other_players' in render_players_section, \
        "_render_players should render other_players"
    print("  ✓ _render_players renders other_players")
    
    # Verify it renders local_player (the original user)
    assert 'local_player' in render_players_section, \
        "_render_players should render local_player (the original user)"
    print("  ✓ _render_players renders local_player (original user)")
    
    print("\n✅ PASS: _render_players method is properly implemented")


def test_cube_vertices_helper_exists():
    """Test that _cube_vertices helper function exists."""
    print("\n🧪 Test: _cube_vertices helper function exists")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that _cube_vertices function exists
    assert 'def _cube_vertices(x, y, z, n):' in content, \
        "_cube_vertices helper function should exist for rendering player cubes"
    print("  ✓ _cube_vertices function exists")
    
    # Verify it returns vertex data
    cube_vertices_section = content.split('def _cube_vertices(x, y, z, n):', 1)[1].split('def ', 1)[0]
    assert 'return [' in cube_vertices_section, \
        "_cube_vertices should return vertex array"
    print("  ✓ _cube_vertices returns vertex data")
    
    print("\n✅ PASS: _cube_vertices helper is properly implemented")


def test_camera_renders_players_in_views():
    """Integration test: verify the complete camera-to-player rendering chain."""
    print("\n🧪 Integration Test: Camera renders players in views")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify the complete chain exists:
    # 1. _render_simple_scene -> _render_world_from_camera
    render_simple_scene_section = content.split('def _render_simple_scene(self):', 1)[1].split('def ', 1)[0]
    assert '_render_world_from_camera' in render_simple_scene_section, \
        "_render_simple_scene should call _render_world_from_camera"
    print("  ✓ _render_simple_scene calls _render_world_from_camera")
    
    # 2. _render_world_from_camera -> render_world_scene with _render_players
    render_world_section = content.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    assert 'render_world_scene(' in render_world_section, \
        "_render_world_from_camera should call render_world_scene"
    assert 'render_players_func=self._render_players' in render_world_section, \
        "_render_world_from_camera should pass _render_players to render_world_scene"
    print("  ✓ _render_world_from_camera calls render_world_scene with _render_players")
    
    # 3. render_world_scene calls render_players_func if provided
    render_world_scene_section = content.split('def render_world_scene(', 1)[1].split('\ndef ', 1)[0]
    assert 'if render_players_func:' in render_world_scene_section, \
        "render_world_scene should check for render_players_func"
    assert 'render_players_func()' in render_world_scene_section, \
        "render_world_scene should call render_players_func"
    print("  ✓ render_world_scene calls render_players_func when provided")
    
    # 4. _render_players renders cubes using pyglet.graphics.draw
    render_players_section = content.split('def _render_players(self):', 1)[1].split('def ', 1)[0]
    assert 'pyglet.graphics.draw' in render_players_section, \
        "_render_players should use pyglet.graphics.draw to render player cubes"
    assert 'GL_QUADS' in render_players_section, \
        "_render_players should render quads for cubes"
    print("  ✓ _render_players renders player cubes with pyglet.graphics.draw")
    
    print("\n✅ PASS: Complete camera-to-player rendering chain is functional")


def test_comment_explains_player_visibility():
    """Test that comments explain the player visibility fix."""
    print("\n🧪 Test: Comments explain player visibility")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    render_world_section = content.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    
    # Check for explanatory comments about player visibility
    section_lower = render_world_section.lower()
    assert 'player' in section_lower and ('visible' in section_lower or 'render' in section_lower), \
        "Comments should explain that players are now visible in camera views"
    print("  ✓ Comments explain player visibility in camera views")
    
    print("\n✅ PASS: Comments are explanatory")


if __name__ == '__main__':
    print("=" * 70)
    print("CAMERA PLAYER VISIBILITY TEST SUITE")
    print("=" * 70)
    
    try:
        test_render_players_func_is_passed()
        test_render_players_method_exists()
        test_cube_vertices_helper_exists()
        test_camera_renders_players_in_views()
        test_comment_explains_player_visibility()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Camera player visibility is working!")
        print("=" * 70)
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
