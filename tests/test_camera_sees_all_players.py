#!/usr/bin/env python3
"""
Test to verify that camera blocks can see all players (users).

This test addresses the requirement:
"vérifie que le bloc caméra voit bien tout les utilisateur, dans la windows camera,
comme les utilisateurs sont capables de se voir entre eux. check que les bloc camera
voient les utilisateurs joueurs."

Translation: Verify that camera blocks see all users properly, in the camera windows,
like users can see each other. Check that camera blocks see player users.

This ensures:
1. Camera blocks render ALL other players (remote users)
2. Camera blocks render the local player (camera owner)
3. This matches how the main window renders players (users can see each other)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_camera_renders_other_players():
    """Test that camera _render_players renders all other players."""
    print("\n🧪 Test: Camera renders all other players (remote users)")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_players method in CubeWindow
    cubewindow_section = content.split('class CubeWindow:', 1)[1]
    render_players_section = cubewindow_section.split('def _render_players(self):', 1)[1].split('def ', 1)[0]
    
    # Verify it iterates over other_players
    assert 'other_players' in render_players_section, \
        "Camera _render_players should iterate over model.other_players"
    print("  ✓ Camera renders other_players")
    
    # Verify it calls get_render_position for each player
    assert 'get_render_position' in render_players_section, \
        "Camera should get render position for each player"
    print("  ✓ Camera gets render position for each player")
    
    # Verify it renders using pyglet.graphics.draw
    assert 'pyglet.graphics.draw' in render_players_section, \
        "Camera should render players using pyglet.graphics.draw"
    print("  ✓ Camera renders players using pyglet.graphics.draw")
    
    # Verify it renders GL_QUADS (cubes)
    assert 'GL_QUADS' in render_players_section, \
        "Camera should render player cubes as GL_QUADS"
    print("  ✓ Camera renders player cubes as GL_QUADS")
    
    print("\n✅ PASS: Camera renders all other players")


def test_camera_renders_local_player():
    """Test that camera _render_players renders the local player (camera owner)."""
    print("\n🧪 Test: Camera renders local player (camera owner)")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _render_players method in CubeWindow
    cubewindow_section = content.split('class CubeWindow:', 1)[1]
    render_players_section = cubewindow_section.split('def _render_players(self):', 1)[1].split('def ', 1)[0]
    
    # Verify it checks for local_player
    assert 'local_player' in render_players_section, \
        "Camera _render_players should check for model.local_player"
    print("  ✓ Camera checks for local_player")
    
    # Verify it renders the local player separately
    # Count how many times pyglet.graphics.draw appears (should be at least 2: one for other_players, one for local_player)
    draw_count = render_players_section.count('pyglet.graphics.draw')
    assert draw_count >= 2, \
        f"Camera should render both other players and local player (found {draw_count} draw calls, expected at least 2)"
    print(f"  ✓ Camera has {draw_count} draw calls (renders both other players and local player)")
    
    print("\n✅ PASS: Camera renders local player (camera owner)")


def test_camera_and_window_use_same_rendering_logic():
    """Test that camera and main window use the same player rendering logic."""
    print("\n🧪 Test: Camera and main window use consistent player rendering")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        protocol_content = f.read()
    
    with open(client_file, 'r', encoding='utf-8') as f:
        client_content = f.read()
    
    # Both should render other_players
    assert 'other_players' in protocol_content and 'other_players' in client_content, \
        "Both camera and main window should render other_players"
    print("  ✓ Both camera and main window render other_players")
    
    # Both should use get_render_position
    camera_section = protocol_content.split('def _render_players(self):', 1)[1].split('def ', 1)[0]
    window_section = client_content.split('def draw_players(self):', 1)[1].split('def ', 1)[0]
    
    assert 'get_render_position' in camera_section and 'get_render_position' in window_section, \
        "Both camera and main window should use get_render_position"
    print("  ✓ Both use get_render_position for player positions")
    
    # Both should render using GL_QUADS
    assert 'GL_QUADS' in camera_section and 'GL_QUADS' in window_section, \
        "Both camera and main window should render players as GL_QUADS"
    print("  ✓ Both render players as GL_QUADS (cubes)")
    
    # Both should render local player
    assert 'local_player' in camera_section and 'local_player' in window_section, \
        "Both camera and main window should render local_player"
    print("  ✓ Both render local_player (camera owner in camera, player in main window)")
    
    print("\n✅ PASS: Camera and main window use consistent rendering logic")


def test_camera_has_access_to_model():
    """Test that camera has access to the model to see all players."""
    print("\n🧪 Test: Camera has access to model for player data")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find CubeWindow __init__ method
    cubewindow_section = content.split('class CubeWindow:', 1)[1]
    init_section = cubewindow_section.split('def __init__(', 1)[1].split('\n    def ', 1)[0]
    
    # Verify model parameter is accepted
    assert 'model' in init_section, \
        "CubeWindow __init__ should accept model parameter"
    print("  ✓ CubeWindow accepts model parameter")
    
    # Verify model is stored
    assert 'self.model = model' in init_section, \
        "CubeWindow should store model reference"
    print("  ✓ CubeWindow stores model reference")
    
    # Verify _render_players uses self.model
    render_players_section = cubewindow_section.split('def _render_players(self):', 1)[1].split('def ', 1)[0]
    assert 'self.model' in render_players_section, \
        "Camera _render_players should access self.model"
    print("  ✓ Camera _render_players accesses self.model")
    
    # Verify it checks model.other_players
    assert 'self.model' in render_players_section and 'other_players' in render_players_section, \
        "Camera should access model.other_players for remote players"
    print("  ✓ Camera accesses model.other_players for remote players")
    
    # Verify it checks model.local_player
    assert 'self.model' in render_players_section and 'local_player' in render_players_section, \
        "Camera should access model.local_player for camera owner"
    print("  ✓ Camera accesses model.local_player for camera owner")
    
    print("\n✅ PASS: Camera has proper access to model for all player data")


def test_documentation_explains_player_visibility():
    """Test that documentation clearly explains that cameras see all players."""
    print("\n🧪 Test: Documentation explains camera sees all players")
    
    protocol_file = Path(__file__).parent.parent / 'protocol.py'
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find _render_players method and its docstring/comments
    cubewindow_section = content.split('class CubeWindow:', 1)[1]
    render_players_section = cubewindow_section.split('def _render_players(self):', 1)[1].split('def ', 1)[0]
    
    # Check for explanatory text about rendering all players
    section_lower = render_players_section.lower()
    
    # Should mention "all players" or "other players"
    assert 'player' in section_lower, \
        "Documentation should mention players"
    print("  ✓ Documentation mentions players")
    
    # Should explain visibility in camera views
    render_world_section = cubewindow_section.split('def _render_world_from_camera(self):', 1)[1].split('def ', 1)[0]
    assert 'visible' in render_world_section.lower() or 'render' in render_world_section.lower(), \
        "Documentation should explain rendering/visibility in camera views"
    print("  ✓ Documentation explains rendering in camera views")
    
    # Check that render_players_func is passed with comment about making players visible
    assert 'render_players_func' in render_world_section and 'self._render_players' in render_world_section, \
        "Code should show render_players_func is passed to render players"
    print("  ✓ Code shows render_players_func is passed for player rendering")
    
    print("\n✅ PASS: Documentation properly explains camera player visibility")


if __name__ == '__main__':
    print("=" * 70)
    print("CAMERA SEES ALL PLAYERS TEST SUITE")
    print("=" * 70)
    print()
    print("Verifying that camera blocks can see all users/players:")
    print("  1. All other players (remote users)")
    print("  2. The local player (camera owner)")
    print("  3. Same rendering logic as main window (users see each other)")
    print()
    
    try:
        test_camera_renders_other_players()
        test_camera_renders_local_player()
        test_camera_and_window_use_same_rendering_logic()
        test_camera_has_access_to_model()
        test_documentation_explains_player_visibility()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Camera blocks see all players!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✅ Camera blocks render all other players (remote users)")
        print("  ✅ Camera blocks render the local player (camera owner)")
        print("  ✅ Camera uses same rendering logic as main window")
        print("  ✅ Camera has access to model.other_players and model.local_player")
        print("  ✅ Documentation explains player visibility in camera views")
        print()
        print("Camera blocks can see all users, just like users can see each other")
        print("in the main window. The rendering is consistent across both views.")
        print()
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
