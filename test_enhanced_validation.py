#!/usr/bin/env python3
"""
Test the enhanced position validation and defensive measures.
This test ensures that the cube positioning system is robust against invalid inputs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, Cube
from client import ClientModel, cube_vertices

def test_position_validation():
    """Test position validation in protocol."""
    print("🧪 Testing position validation in protocol...")
    
    # Test valid position updates
    player = PlayerState("test", (0, 0, 0), (0, 0))
    
    valid_positions = [
        (0, 0, 0),
        (1.5, 2.5, 3.5),
        (-1, -2, -3),
        (100, 200, 300),
    ]
    
    for pos in valid_positions:
        try:
            player.update_position(pos)
            render_pos = player.get_render_position()
            cube_bottom = render_pos[1] - player.size
            print(f"   ✅ Valid position {pos}: cube bottom at {cube_bottom}")
            
            # Verify cube bottom equals player Y
            if abs(cube_bottom - pos[1]) < 0.001:
                print(f"      ✅ Correct cube positioning")
            else:
                print(f"      ❌ Incorrect cube positioning! Expected: {pos[1]}, got: {cube_bottom}")
                return False
                
        except Exception as e:
            print(f"   ❌ Unexpected error with valid position {pos}: {e}")
            return False
    
    # Test invalid position updates
    invalid_positions = [
        (1, 2),  # Too few coordinates
        (1, 2, 3, 4),  # Too many coordinates
        ("a", "b", "c"),  # Non-numeric
        (1, "b", 3),  # Mixed types
        None,  # None
        "invalid",  # String
    ]
    
    for pos in invalid_positions:
        try:
            player.update_position(pos)
            print(f"   ❌ Should have rejected invalid position: {pos}")
            return False
        except (ValueError, TypeError) as e:
            print(f"   ✅ Correctly rejected invalid position {pos}: {type(e).__name__}")
        except Exception as e:
            print(f"   ❌ Unexpected error type for {pos}: {e}")
            return False
    
    return True

def test_client_model_validation():
    """Test validation in client model."""
    print("\n🧪 Testing client model validation...")
    
    model = ClientModel()
    
    # Test valid local player creation
    try:
        player = model.create_local_player("valid_player", (0, 0, 0), (0, 0), "ValidPlayer")
        print(f"   ✅ Created valid local player at {player.position}")
        
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        print(f"   ✅ Render position: {render_pos}, cube bottom: {cube_bottom}")
        
    except Exception as e:
        print(f"   ❌ Failed to create valid local player: {e}")
        return False
    
    # Test invalid local player creation
    invalid_cases = [
        ("short_pos", (0, 0), (0, 0), "Position too short"),
        ("long_pos", (0, 0, 0, 0), (0, 0), "Position too long"),
        ("string_pos", "invalid", (0, 0), "String position"),
        ("mixed_pos", (1, "b", 3), (0, 0), "Mixed position types"),
        ("short_rot", (0, 0, 0), (0,), "Rotation too short"),
        ("long_rot", (0, 0, 0), (0, 0, 0), "Rotation too long"),
        ("string_rot", (0, 0, 0), "invalid", "String rotation"),
    ]
    
    for case_name, position, rotation, description in invalid_cases:
        try:
            model.create_local_player(case_name, position, rotation, "TestPlayer")
            print(f"   ❌ Should have rejected {description}")
            return False
        except (ValueError, TypeError) as e:
            print(f"   ✅ Correctly rejected {description}: {type(e).__name__}")
        except Exception as e:
            print(f"   ❌ Unexpected error for {description}: {e}")
            return False
    
    # Test valid cube addition
    try:
        valid_cube = PlayerState("valid_remote", (5, 10, 15), (90, 45), "ValidRemote")
        model.add_cube(valid_cube)
        print(f"   ✅ Added valid remote cube at {valid_cube.position}")
        
        render_pos = valid_cube.get_render_position()
        cube_bottom = render_pos[1] - valid_cube.size
        print(f"   ✅ Remote cube render position: {render_pos}, cube bottom: {cube_bottom}")
        
    except Exception as e:
        print(f"   ❌ Failed to add valid cube: {e}")
        return False
    
    # Test invalid cube addition
    invalid_cubes = [
        PlayerState("invalid_pos1", (1, 2), (0, 0), "ShortPos"),  # Will fail during creation
    ]
    
    # Create cubes with invalid positions after creation
    try:
        bad_cube = Cube("bad_cube", (0, 0, 0))
        bad_cube.position = "invalid"  # Corrupt position
        model.add_cube(bad_cube)
        print(f"   ❌ Should have rejected cube with corrupted position")
        return False
    except (ValueError, TypeError) as e:
        print(f"   ✅ Correctly rejected cube with corrupted position: {type(e).__name__}")
    except Exception as e:
        print(f"   ❌ Unexpected error for corrupted cube: {e}")
        return False
    
    return True

def test_cube_vertices_validation():
    """Test cube vertices validation."""
    print("\n🧪 Testing cube vertices validation...")
    
    # Test valid vertex generation
    valid_cases = [
        (0, 0, 0, 0.5),
        (10, 20, 30, 1.0),
        (-5, -10, -15, 0.25),
        (1.5, 2.5, 3.5, 0.75),
    ]
    
    for x, y, z, n in valid_cases:
        try:
            vertices = cube_vertices(x, y, z, n)
            print(f"   ✅ Generated vertices for cube at ({x}, {y}, {z}) size {n}: {len(vertices)} values")
            
            # Verify we got the expected number of vertices
            if len(vertices) != 72:  # 24 vertices * 3 coordinates
                print(f"   ❌ Wrong number of vertices! Expected 72, got {len(vertices)}")
                return False
                
        except Exception as e:
            print(f"   ❌ Failed to generate vertices for valid case ({x}, {y}, {z}, {n}): {e}")
            return False
    
    # Test invalid vertex generation
    invalid_cases = [
        ("string", 0, 0, 0.5, "String X coordinate"),
        (0, "string", 0, 0.5, "String Y coordinate"),
        (0, 0, "string", 0.5, "String Z coordinate"),
        (0, 0, 0, "string", "String size"),
        (0, 0, 0, 0, "Zero size"),
        (0, 0, 0, -1, "Negative size"),
        (None, 0, 0, 0.5, "None coordinate"),
    ]
    
    for x, y, z, n, description in invalid_cases:
        try:
            vertices = cube_vertices(x, y, z, n)
            print(f"   ❌ Should have rejected {description}")
            return False
        except (ValueError, TypeError) as e:
            print(f"   ✅ Correctly rejected {description}: {type(e).__name__}")
        except Exception as e:
            print(f"   ❌ Unexpected error for {description}: {e}")
            return False
    
    return True

def test_render_position_consistency():
    """Test render position consistency after validation changes."""
    print("\n🧪 Testing render position consistency...")
    
    model = ClientModel()
    
    # Test various positions to ensure consistency
    test_positions = [
        (0, 0, 0),
        (1, 1, 1),
        (10, 20, 30),
        (-5, -10, -15),
        (1.5, 2.5, 3.5),
        (100.123, 200.456, 300.789),
    ]
    
    for i, pos in enumerate(test_positions):
        try:
            # Create both local and remote players at same position
            local_player = model.create_local_player(f"local_{i}", pos, (0, 0), f"Local{i}")
            remote_player = PlayerState(f"remote_{i}", pos, (0, 0), f"Remote{i}")
            model.add_cube(remote_player)
            
            # Get render positions
            local_render = local_player.get_render_position()
            remote_render = remote_player.get_render_position()
            
            # Calculate cube bottoms
            local_bottom = local_render[1] - local_player.size
            remote_bottom = remote_render[1] - remote_player.size
            
            print(f"   Position {pos}:")
            print(f"     Local render: {local_render}, bottom: {local_bottom}")
            print(f"     Remote render: {remote_render}, bottom: {remote_bottom}")
            
            # Verify consistency
            if abs(local_bottom - pos[1]) > 0.001:
                print(f"     ❌ Local cube bottom inconsistent! Expected: {pos[1]}, got: {local_bottom}")
                return False
            
            if abs(remote_bottom - pos[1]) > 0.001:
                print(f"     ❌ Remote cube bottom inconsistent! Expected: {pos[1]}, got: {remote_bottom}")
                return False
            
            if abs(local_bottom - remote_bottom) > 0.001:
                print(f"     ❌ Local and remote cube bottoms don't match!")
                return False
            
            print(f"     ✅ Consistent positioning")
            
        except Exception as e:
            print(f"   ❌ Error testing position {pos}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🎮 TESTING ENHANCED POSITION VALIDATION")
    print("=" * 50)
    print("Testing defensive measures against floating cubes...")
    print()
    
    try:
        success = True
        success &= test_position_validation()
        success &= test_client_model_validation()
        success &= test_cube_vertices_validation()
        success &= test_render_position_consistency()
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 ALL VALIDATION TESTS PASSED!")
            print("✅ Position validation is robust")
            print("✅ Client model validation works correctly")
            print("✅ Cube vertices validation prevents errors")
            print("✅ Render position consistency maintained")
            print()
            print("🛡️ DEFENSIVE MEASURES SUCCESSFULLY IMPLEMENTED!")
            print("📝 The system now has strong protection against floating cubes.")
            print("=" * 50)
        else:
            print("\n❌ VALIDATION TESTS FAILED!")
            print("Check the failed tests above for specific problems.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)