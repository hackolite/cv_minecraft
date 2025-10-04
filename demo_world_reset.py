#!/usr/bin/env python3
"""
Demonstration script showing the world reset feature in action.
This script shows the before and after state of the world.
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise

from server import GameWorld
from protocol import BlockType

def count_blocks_by_type(world):
    """Count blocks by type in the world."""
    counts = {}
    for pos, block_data in world.world.items():
        if isinstance(block_data, dict):
            block_type = block_data.get("type")
        else:
            block_type = block_data
        
        counts[block_type] = counts.get(block_type, 0) + 1
    
    return counts

def main():
    print("=" * 70)
    print("WORLD RESET FEATURE DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Create world WITHOUT reset
    print("📦 Creating world WITHOUT reset (normal startup)...")
    world_normal = GameWorld(reset_to_natural=False)
    
    counts_before = count_blocks_by_type(world_normal)
    total_before = len(world_normal.world)
    
    print(f"\n✅ World created with {total_before:,} blocks")
    print("\n📊 Block distribution BEFORE reset:")
    print("-" * 70)
    
    # Sort by count descending
    for block_type, count in sorted(counts_before.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_before) * 100
        bar = "█" * min(50, int(percentage))
        print(f"  {block_type:10s}: {count:6,} blocks ({percentage:5.2f}%) {bar}")
    
    print("\n" + "=" * 70)
    print()
    
    # Create world WITH reset
    print("🔄 Creating world WITH reset (--reset-world flag)...")
    world_reset = GameWorld(reset_to_natural=True)
    
    counts_after = count_blocks_by_type(world_reset)
    total_after = len(world_reset.world)
    
    print(f"\n✅ World created with {total_after:,} blocks")
    print("\n📊 Block distribution AFTER reset:")
    print("-" * 70)
    
    # Sort by count descending
    for block_type, count in sorted(counts_after.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_after) * 100
        bar = "█" * min(50, int(percentage))
        print(f"  {block_type:10s}: {count:6,} blocks ({percentage:5.2f}%) {bar}")
    
    print("\n" + "=" * 70)
    print()
    
    # Show what was removed
    removed = total_before - total_after
    print(f"🗑️  REMOVED: {removed} blocks ({(removed/total_before)*100:.2f}% of total)")
    print("\n📋 Removed block types:")
    print("-" * 70)
    
    for block_type in sorted(counts_before.keys()):
        before = counts_before.get(block_type, 0)
        after = counts_after.get(block_type, 0)
        if before > after:
            removed_count = before - after
            print(f"  {block_type:10s}: {removed_count:6,} blocks removed")
    
    print("\n" + "=" * 70)
    print()
    
    # Summary
    print("📝 SUMMARY:")
    print("-" * 70)
    print(f"  Blocks before reset: {total_before:,}")
    print(f"  Blocks after reset:  {total_after:,}")
    print(f"  Blocks removed:      {removed:,}")
    print()
    print("  ✅ Only natural terrain remains (grass, sand, stone, water, wood, leaf)")
    print("  ❌ All cameras, user blocks, cats, and other player blocks removed")
    print()
    print("=" * 70)
    print("\n💡 To use this feature, start the server with:")
    print("   python server.py --reset-world")
    print()

if __name__ == "__main__":
    main()
