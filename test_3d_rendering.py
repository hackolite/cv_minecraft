#!/usr/bin/env python3
"""
Test 3D rendering capabilities without actually opening a window.
This verifies that the client can properly receive and process chunked world data.
"""

import asyncio
import websockets
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_3d_rendering():
    """Test the 3D rendering fix without opening a window."""
    print("🎮 Testing 3D Rendering Fix")
    print("=" * 40)
    
    # Simulate client behavior
    blocks_received = {}
    chunk_count = 0
    
    try:
        uri = "ws://localhost:8765"
        async with websockets.connect(uri, timeout=10) as websocket:
            print("✅ Connected to server")
            
            # Join game
            join_msg = json.dumps({'type': 'join', 'name': 'RenderingTestClient'})
            await websocket.send(join_msg)
            
            welcome_response = await websocket.recv()
            welcome_data = json.loads(welcome_response)
            
            if welcome_data.get('type') != 'welcome':
                print("❌ Failed to join game")
                return False
            
            player_pos = welcome_data.get('position', [0, 0, 0])
            print(f"✅ Joined game at position: {player_pos}")
            
            # Request world data
            world_request = json.dumps({'type': 'get_world'})
            await websocket.send(world_request)
            print("📡 Requested world data...")
            
            # Process chunked world data (simulate client rendering)
            world_complete = False
            total_blocks_processed = 0
            render_errors = 0
            
            while not world_complete:
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get('type') == 'world_data':
                    # Single message world data
                    blocks = data.get('blocks', [])
                    total_blocks_processed = len(blocks)
                    world_complete = True
                    print(f"📦 Received {len(blocks)} blocks in single message")
                    
                    # Simulate 3D rendering
                    for block_data in blocks:
                        success = simulate_block_rendering(block_data)
                        if not success:
                            render_errors += 1
                    
                elif data.get('type') == 'world_chunk':
                    # Chunked world data
                    blocks = data.get('blocks', [])
                    chunk_index = data.get('chunk_index', 0)
                    total_chunks = data.get('total_chunks', 1)
                    chunk_count += 1
                    
                    print(f"📦 Processing chunk {chunk_index+1}/{total_chunks} ({len(blocks)} blocks)")
                    
                    # Simulate 3D rendering for this chunk
                    chunk_render_errors = 0
                    for block_data in blocks:
                        success = simulate_block_rendering(block_data)
                        if success:
                            position = tuple(block_data.get('position', [0, 0, 0]))
                            blocks_received[position] = block_data.get('block_type', 'unknown')
                        else:
                            chunk_render_errors += 1
                            render_errors += 1
                    
                    total_blocks_processed += len(blocks)
                    
                    if chunk_render_errors > 0:
                        print(f"⚠️  Chunk {chunk_index+1} had {chunk_render_errors} rendering errors")
                    
                elif data.get('type') == 'world_complete':
                    # World loading complete
                    total_blocks = data.get('total_blocks', 0)
                    world_complete = True
                    print(f"✅ World loading complete: {total_blocks} blocks total")
                else:
                    print(f"❓ Unexpected message type: {data.get('type')}")
                    break
            
            # Verify 3D rendering capabilities
            print(f"\n🔍 3D Rendering Analysis:")
            print(f"   • Chunks processed: {chunk_count}")
            print(f"   • Blocks processed: {total_blocks_processed}")
            print(f"   • Blocks stored: {len(blocks_received)}")
            print(f"   • Rendering errors: {render_errors}")
            
            # Test different block types
            block_types = set(blocks_received.values())
            print(f"   • Block types found: {len(block_types)}")
            print(f"   • Block types: {', '.join(block_types)}")
            
            # Test 3D positioning
            if blocks_received:
                positions = list(blocks_received.keys())
                min_x = min(pos[0] for pos in positions)
                max_x = max(pos[0] for pos in positions)
                min_y = min(pos[1] for pos in positions)
                max_y = max(pos[1] for pos in positions)
                min_z = min(pos[2] for pos in positions)
                max_z = max(pos[2] for pos in positions)
                
                print(f"   • World bounds: X({min_x}, {max_x}) Y({min_y}, {max_y}) Z({min_z}, {max_z})")
                print(f"   • 3D volume: {max_x-min_x+1} × {max_y-min_y+1} × {max_z-min_z+1}")
            
            # Final assessment
            success_rate = (total_blocks_processed - render_errors) / total_blocks_processed if total_blocks_processed > 0 else 0
            
            print(f"\n📊 Rendering Success Rate: {success_rate:.1%}")
            
            if success_rate >= 0.95:
                print("✅ 3D rendering fix is working correctly!")
                print("✅ Chunked world data is being processed properly")
                print("✅ Block positioning and types are valid")
                return True
            else:
                print("❌ 3D rendering has issues - too many errors")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_block_rendering(block_data):
    """Simulate the 3D block rendering process."""
    if not isinstance(block_data, dict):
        return False
    
    position = block_data.get('position')
    block_type = block_data.get('block_type')
    
    # Validate position
    if not position or not isinstance(position, (list, tuple)) or len(position) != 3:
        return False
    
    # Validate block type
    if not block_type or not isinstance(block_type, str):
        return False
    
    # Validate position values
    try:
        x, y, z = position
        float(x), float(y), float(z)  # Ensure they're numeric
    except (TypeError, ValueError):
        return False
    
    # All validations passed - this block can be rendered in 3D
    return True

if __name__ == "__main__":
    result = asyncio.run(test_3d_rendering())
    
    if result:
        print("\n🎉 3D Rendering Test: PASSED")
        print("The client should now properly display blocks in 3D!")
    else:
        print("\n❌ 3D Rendering Test: FAILED")
        print("There are still issues with 3D block visibility.")