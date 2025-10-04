#!/usr/bin/env python3
"""
Test CAT block selection via mouse wheel in client inventory.
"""

import sys
sys.path.insert(0, '..')

from protocol import BlockType

def test_cat_in_inventory():
    """Test that CAT block type is included in the inventory."""
    print("🧪 Testing CAT block in inventory...")
    
    # Import here to avoid display issues during import
    import os
    os.environ['DISPLAY'] = ':99'
    
    # Import the inventory from minecraft_client_fr
    import minecraft_client_fr
    
    # Create a mock window to check inventory
    # We need to check the class definition
    import inspect
    source = inspect.getsource(minecraft_client_fr.MinecraftWindow.__init__)
    
    # Check if CAT is in the inventory definition
    assert 'BlockType.CAT' in source, "BlockType.CAT should be in inventory definition"
    print("  ✅ CAT block found in inventory source code")
    print("✅ CAT block in inventory test passed\n")

def test_cat_block_selection():
    """Test that CAT can be selected (check BlockType definition)."""
    print("🧪 Testing CAT block can be selected...")
    
    # Verify CAT is a valid block type
    assert hasattr(BlockType, 'CAT'), "BlockType.CAT should exist"
    assert BlockType.CAT == "cat", "BlockType.CAT should equal 'cat'"
    
    print("  ✅ CAT block type is valid for selection")
    print("✅ CAT block selection test passed\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing CAT Block Inventory Selection")
    print("=" * 60 + "\n")
    
    try:
        test_cat_in_inventory()
        test_cat_block_selection()
        
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
