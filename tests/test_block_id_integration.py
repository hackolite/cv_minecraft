#!/usr/bin/env python3
"""
Integration test for block metadata with block_id queries.
Tests the server's ability to query blocks by block_id.
"""

import asyncio
import websockets
import json
import sys

SERVER_URI = "ws://localhost:8765"

async def test_query_by_block_id():
    """Test querying blocks using block_id in view query."""
    print("🧪 Testing query by block_id...")
    
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Join the game
            join_msg = {"type": "player_join", "data": {"name": "BlockIDTestUser"}}
            await ws.send(json.dumps(join_msg))
            print("  ✅ Sent player_join")
            
            # Receive world_init
            response = await ws.recv()
            data = json.loads(response)
            assert data["type"] == "world_init"
            print(f"  ✅ Received world_init")
            
            # Skip world chunks
            chunk_count = 0
            while True:
                response = await ws.recv()
                data = json.loads(response)
                if data["type"] == "world_chunk":
                    chunk_count += 1
                elif data["type"] == "player_list":
                    print(f"  ✅ Received {chunk_count} world chunks")
                    break
            
            # Get cameras list to find a camera block_id
            cameras_request = {"type": "get_cameras_list", "data": {}}
            await ws.send(json.dumps(cameras_request))
            print("  ✅ Sent get_cameras_list")
            
            response = await ws.recv()
            data = json.loads(response)
            assert data["type"] == "cameras_list"
            cameras = data["data"]["cameras"]
            print(f"  ✅ Received {len(cameras)} cameras")
            
            # Verify cameras have block_id and collision attributes
            if len(cameras) > 0:
                camera = cameras[0]
                assert "block_id" in camera
                assert "collision" in camera
                assert camera["block_id"] is not None
                assert camera["collision"] == True
                print(f"  ✅ Camera has block_id={camera['block_id']}, collision={camera['collision']}")
                
                # Test querying blocks from camera's perspective using block_id
                blocks_request = {
                    "type": "get_blocks_list",
                    "data": {
                        "query_type": "view",
                        "block_id": camera["block_id"],  # Use block_id instead of position
                        "rotation": [0, 0],
                        "view_distance": 30.0
                    }
                }
                await ws.send(json.dumps(blocks_request))
                print(f"  ✅ Sent get_blocks_list with block_id={camera['block_id']}")
                
                response = await ws.recv()
                data = json.loads(response)
                assert data["type"] == "blocks_list"
                blocks = data["data"]["blocks"]
                print(f"  ✅ Received {len(blocks)} blocks from camera perspective")
                
                # Verify blocks have metadata
                if len(blocks) > 0:
                    block = blocks[0]
                    assert "position" in block
                    assert "block_type" in block
                    assert "block_id" in block
                    assert "collision" in block
                    assert "distance" in block
                    print(f"  ✅ Block metadata: type={block['block_type']}, collision={block['collision']}")
            else:
                print("  ⚠️  No cameras found")
            
            print("✅ Query by block_id test passed\n")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_blocks_metadata():
    """Test that all blocks have collision and block_id attributes."""
    print("🧪 Testing blocks metadata...")
    
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Join the game
            join_msg = {"type": "player_join", "data": {"name": "MetadataTestUser"}}
            await ws.send(json.dumps(join_msg))
            
            # Receive world_init
            response = await ws.recv()
            data = json.loads(response)
            
            # Skip world chunks
            while True:
                response = await ws.recv()
                data = json.loads(response)
                if data["type"] == "player_list":
                    break
            
            # Get blocks in a region
            blocks_request = {
                "type": "get_blocks_list",
                "data": {
                    "query_type": "region",
                    "center": [64, 100, 64],
                    "radius": 10.0
                }
            }
            await ws.send(json.dumps(blocks_request))
            print("  ✅ Sent get_blocks_list (region)")
            
            response = await ws.recv()
            data = json.loads(response)
            assert data["type"] == "blocks_list"
            blocks = data["data"]["blocks"]
            print(f"  ✅ Received {len(blocks)} blocks")
            
            # Verify all blocks have required metadata
            for block in blocks[:10]:  # Check first 10
                assert "position" in block
                assert "block_type" in block
                assert "block_id" in block  # May be None for non-camera/user blocks
                assert "collision" in block
                
                # Verify collision is boolean
                assert isinstance(block["collision"], bool)
            
            print("  ✅ All blocks have required metadata attributes")
            print("✅ Blocks metadata test passed\n")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all integration tests."""
    print("🚀 Block Metadata Integration Tests")
    print("=" * 60)
    
    try:
        # Wait a moment for server to be ready
        await asyncio.sleep(1)
        
        result1 = await test_query_by_block_id()
        result2 = await test_blocks_metadata()
        
        if result1 and result2:
            print("=" * 60)
            print("✅ ALL INTEGRATION TESTS PASSED!")
            return 0
        else:
            print("=" * 60)
            print("❌ SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
