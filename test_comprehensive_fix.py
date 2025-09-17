#!/usr/bin/env python3
"""
Test to verify the collision fix works for various scenarios and ensure proper positioning
"""

def normalize(position):
    """Normalize position to block coordinates."""
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

FACES = [
    (0, 1, 0),    # Up
    (0, -1, 0),   # Down  
    (-1, 0, 0),   # Left
    (1, 0, 0),    # Right
    (0, 0, 1),    # Forward
    (0, 0, -1),   # Backward
]

try:
    xrange
except NameError:
    xrange = range

def collide_fixed(position, height, world):
    """Fixed collision detection"""
    pad = 0.25
    p = list(position)
    np = normalize(position)
    collision_types = {"top": False, "bottom": False, "right": False, "left": False}
    
    for face in FACES:
        for i in xrange(3):
            if not face[i]:
                continue
            d = (p[i] - np[i]) * face[i]
            # FIX: Allow downward collision detection even with small d values
            if d < pad and not (face == (0, -1, 0) and i == 1):
                continue
                
            for dy in xrange(height):
                op = list(np)
                op[1] -= dy
                
                # COLLISION FIX: For downward collision, check the block the player is standing on
                if face == (0, -1, 0) and i == 1:
                    # For downward collision, we need to check the block below the player's feet
                    # Instead of adding face[i] (-1), we check the floor of the current position
                    op[1] = int(p[1]) - dy
                else:
                    op[i] += face[i]
                
                if tuple(op) not in world:
                    continue
                    
                p[i] -= (d - pad) * face[i]
                if face == (0, -1, 0):
                    collision_types["top"] = True
                if face == (0, 1, 0):
                    collision_types["bottom"] = True
                break
    
    return tuple(p), collision_types

def test_comprehensive_scenarios():
    """Test various collision scenarios to ensure the fix works correctly"""
    print("🔧 Comprehensive Collision Fix Test\n")
    
    test_scenarios = [
        {
            "name": "Player on grass block",
            "world": {(0, 10, 0): 'grass'},
            "test_positions": [
                (0.0, 11.0, 0.0),   # Above block
                (0.0, 10.9, 0.0),   # Slightly above
                (0.0, 10.5, 0.0),   # In middle of block
                (0.0, 10.1, 0.0),   # Just above block surface
            ]
        },
        {
            "name": "Player on stone block",
            "world": {(5, 5, 5): 'stone'},
            "test_positions": [
                (5.0, 6.0, 5.0),    # Above block
                (5.0, 5.9, 5.0),    # Slightly above 
                (5.0, 5.5, 5.0),    # In middle of block
                (5.0, 5.1, 5.0),    # Just above block surface
            ]
        },
        {
            "name": "Player on ground level block",
            "world": {(0, 0, 0): 'stone'},
            "test_positions": [
                (0.0, 1.0, 0.0),    # Above block
                (0.0, 0.9, 0.0),    # Slightly above
                (0.0, 0.5, 0.0),    # In middle of block 
                (0.0, 0.1, 0.0),    # Just above block surface
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"🧪 {scenario['name']}")
        print(f"   World: {scenario['world']}")
        
        for pos in scenario['test_positions']:
            result_pos, collisions = collide_fixed(pos, 2, scenario['world'])
            on_ground = collisions["top"]
            
            # Calculate expected position for player standing on top of block
            block_pos = list(scenario['world'].keys())[0]
            expected_y = block_pos[1] + 1.0  # Block top + some clearance
            
            status = "✅" if on_ground else "❌"
            
            print(f"   {pos} -> {result_pos} (ground: {on_ground}) {status}")
            
            # Check if player ends up in a reasonable position
            if on_ground:
                if result_pos[1] < block_pos[1]:
                    print(f"      ⚠️  Player below block level! Block Y={block_pos[1]}, Player Y={result_pos[1]:.3f}")
                elif result_pos[1] > block_pos[1] + 2:
                    print(f"      ⚠️  Player too high above block! Expected ~{expected_y}, got {result_pos[1]:.3f}")
                else:
                    print(f"      ✅ Player positioned correctly above block")
        print()
    
    # Test that grass and stone behave the same
    print("🔍 Grass vs Stone Comparison:")
    grass_world = {(0, 10, 0): 'grass'}
    stone_world = {(0, 10, 0): 'stone'}
    
    test_pos = (0.0, 10.5, 0.0)
    
    grass_result, grass_coll = collide_fixed(test_pos, 2, grass_world)
    stone_result, stone_coll = collide_fixed(test_pos, 2, stone_world)
    
    print(f"   Test position: {test_pos}")
    print(f"   Grass result: {grass_result} (ground: {grass_coll['top']})")
    print(f"   Stone result: {stone_result} (ground: {stone_coll['top']})")
    
    if grass_result == stone_result and grass_coll == stone_coll:
        print("   ✅ Grass and stone behave identically")
    else:
        print("   ❌ Grass and stone behave differently!")
        print(f"      Difference: {grass_result} vs {stone_result}")

if __name__ == "__main__":
    test_comprehensive_scenarios()