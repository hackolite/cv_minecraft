#!/usr/bin/env python3
"""
Test cat block type functionality.
"""

import sys
sys.path.insert(0, '..')

from server import validate_block_type, create_block_data, get_block_collision
from protocol import BlockType

def test_cat_block_type_exists():
    """Test that CAT block type is defined."""
    print("🧪 Testing CAT block type exists...")
    
    assert hasattr(BlockType, 'CAT'), "BlockType.CAT should be defined"
    assert BlockType.CAT == "cat", "BlockType.CAT should equal 'cat'"
    print("  ✅ BlockType.CAT is defined and equals 'cat'")
    print("✅ CAT block type exists test passed\n")

def test_cat_block_validation():
    """Test that CAT block type is valid."""
    print("🧪 Testing CAT block type validation...")
    
    is_valid = validate_block_type(BlockType.CAT)
    assert is_valid, "CAT block type should be valid"
    print("  ✅ CAT block type is valid")
    print("✅ CAT block validation test passed\n")

def test_cat_block_data_creation():
    """Test that create_block_data works with CAT type."""
    print("🧪 Testing CAT block data creation...")
    
    block_data = create_block_data(BlockType.CAT)
    assert block_data["type"] == BlockType.CAT, "Block type should be 'cat'"
    assert block_data["collision"] == True, "CAT block should have collision"
    assert block_data["block_id"] is None, "CAT block should not have block_id by default"
    print("  ✅ CAT block data created correctly")
    
    # Test with block_id
    block_data_with_id = create_block_data(BlockType.CAT, block_id="cat_123")
    assert block_data_with_id["type"] == BlockType.CAT
    assert block_data_with_id["collision"] == True
    assert block_data_with_id["block_id"] == "cat_123"
    print("  ✅ CAT block with block_id created correctly")
    print("✅ CAT block data creation test passed\n")

def test_cat_block_collision():
    """Test that CAT block has collision."""
    print("🧪 Testing CAT block collision...")
    
    has_collision = get_block_collision(BlockType.CAT)
    assert has_collision, "CAT block should have collision"
    print("  ✅ CAT block has collision")
    print("✅ CAT block collision test passed\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing CAT Block Type Implementation")
    print("=" * 60 + "\n")
    
    try:
        test_cat_block_type_exists()
        test_cat_block_validation()
        test_cat_block_data_creation()
        test_cat_block_collision()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
