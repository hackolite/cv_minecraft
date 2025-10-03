#!/usr/bin/env python3
"""
Test for the new query services: cameras, users, and blocks list.
Tests WebSocket endpoints for getting camera positions, user info, and blocks.
"""

import asyncio
import websockets
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"

async def test_get_cameras_list():
    """Test getting list of camera blocks."""
    logging.info("🧪 Testing GET_CAMERAS_LIST service...")
    
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Join the game first
            join_msg = {"type": "player_join", "data": {"name": "CameraTestUser"}}
            await ws.send(json.dumps(join_msg))
            logging.info(f"Sent join -> {join_msg}")
            
            # Receive world_init
            resp = await ws.recv()
            data = json.loads(resp)
            logging.info(f"Received <- {data['type']}")
            assert data["type"] == "world_init", f"Expected world_init, got {data['type']}"
            
            # Skip through chunks until we get player_list
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data["type"] == "player_list":
                    break
                elif data["type"] != "world_chunk":
                    logging.info(f"Skipping message: {data['type']}")
            
            # Now request cameras list
            cameras_request = {"type": "get_cameras_list", "data": {}}
            await ws.send(json.dumps(cameras_request))
            logging.info(f"Sent camera request -> {cameras_request}")
            
            # Receive cameras list
            resp = await ws.recv()
            data = json.loads(resp)
            logging.info(f"Received <- {json.dumps(data, indent=2)}")
            
            assert data["type"] == "cameras_list", f"Expected cameras_list, got {data['type']}"
            cameras = data["data"]["cameras"]
            logging.info(f"✅ Received {len(cameras)} camera blocks")
            
            for camera in cameras:
                pos = camera["position"]
                logging.info(f"   Camera at position: {pos}")
            
            assert len(cameras) > 0, "Expected at least one camera block"
            logging.info("✅ GET_CAMERAS_LIST test passed")
            return True
            
    except Exception as e:
        logging.error(f"❌ GET_CAMERAS_LIST test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_users_list():
    """Test getting list of users with their positions."""
    logging.info("🧪 Testing GET_USERS_LIST service...")
    
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Join the game
            join_msg = {"type": "player_join", "data": {"name": "UserListTestUser"}}
            await ws.send(json.dumps(join_msg))
            
            # Receive world_init
            resp = await ws.recv()
            data = json.loads(resp)
            assert data["type"] == "world_init"
            
            # Skip chunks
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data["type"] == "player_list":
                    break
            
            # Request users list
            users_request = {"type": "get_users_list", "data": {}}
            await ws.send(json.dumps(users_request))
            logging.info(f"Sent users request -> {users_request}")
            
            # Receive users list
            resp = await ws.recv()
            data = json.loads(resp)
            logging.info(f"Received <- {json.dumps(data, indent=2)}")
            
            assert data["type"] == "users_list", f"Expected users_list, got {data['type']}"
            users = data["data"]["users"]
            logging.info(f"✅ Received {len(users)} users")
            
            for user in users:
                logging.info(f"   User: {user['name']} at position {user['position']}, rotation {user['rotation']}")
            
            assert len(users) >= 1, "Expected at least one user (ourselves)"
            logging.info("✅ GET_USERS_LIST test passed")
            return True
            
    except Exception as e:
        logging.error(f"❌ GET_USERS_LIST test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_blocks_list_region():
    """Test getting blocks in a region."""
    logging.info("🧪 Testing GET_BLOCKS_LIST service (region query)...")
    
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Join the game
            join_msg = {"type": "player_join", "data": {"name": "BlocksTestUser"}}
            await ws.send(json.dumps(join_msg))
            
            # Receive world_init
            resp = await ws.recv()
            data = json.loads(resp)
            assert data["type"] == "world_init"
            spawn_position = data["data"]["spawn_position"]
            
            # Skip chunks
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data["type"] == "player_list":
                    break
            
            # Request blocks in region around spawn
            blocks_request = {
                "type": "get_blocks_list", 
                "data": {
                    "query_type": "region",
                    "center": spawn_position,
                    "radius": 20.0
                }
            }
            await ws.send(json.dumps(blocks_request))
            logging.info(f"Sent blocks request -> {blocks_request}")
            
            # Receive blocks list
            resp = await ws.recv()
            data = json.loads(resp)
            logging.info(f"Received blocks_list with {len(data['data']['blocks'])} blocks")
            
            assert data["type"] == "blocks_list", f"Expected blocks_list, got {data['type']}"
            blocks = data["data"]["blocks"]
            
            # Show first 10 blocks
            for i, block in enumerate(blocks[:10]):
                logging.info(f"   Block {i+1}: {block['block_type']} at {block['position']}")
            
            if len(blocks) > 10:
                logging.info(f"   ... and {len(blocks) - 10} more blocks")
            
            assert len(blocks) > 0, "Expected at least some blocks in region"
            logging.info("✅ GET_BLOCKS_LIST (region) test passed")
            return True
            
    except Exception as e:
        logging.error(f"❌ GET_BLOCKS_LIST (region) test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_blocks_list_view():
    """Test getting blocks in view from a position."""
    logging.info("🧪 Testing GET_BLOCKS_LIST service (view query)...")
    
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Join the game
            join_msg = {"type": "player_join", "data": {"name": "ViewTestUser"}}
            await ws.send(json.dumps(join_msg))
            
            # Receive world_init
            resp = await ws.recv()
            data = json.loads(resp)
            assert data["type"] == "world_init"
            spawn_position = data["data"]["spawn_position"]
            
            # Skip chunks
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data["type"] == "player_list":
                    break
            
            # Request blocks visible from spawn position
            blocks_request = {
                "type": "get_blocks_list", 
                "data": {
                    "query_type": "view",
                    "position": spawn_position,
                    "rotation": [0, 0],  # Looking straight ahead
                    "view_distance": 30.0
                }
            }
            await ws.send(json.dumps(blocks_request))
            logging.info(f"Sent view blocks request -> {blocks_request}")
            
            # Receive blocks list
            resp = await ws.recv()
            data = json.loads(resp)
            logging.info(f"Received blocks_list with {len(data['data']['blocks'])} blocks")
            
            assert data["type"] == "blocks_list", f"Expected blocks_list, got {data['type']}"
            blocks = data["data"]["blocks"]
            
            # Show first 10 blocks with distance
            for i, block in enumerate(blocks[:10]):
                distance = block.get('distance', 'N/A')
                logging.info(f"   Block {i+1}: {block['block_type']} at {block['position']} (distance: {distance:.2f})")
            
            if len(blocks) > 10:
                logging.info(f"   ... and {len(blocks) - 10} more blocks")
            
            assert len(blocks) > 0, "Expected at least some blocks in view"
            logging.info("✅ GET_BLOCKS_LIST (view) test passed")
            return True
            
    except Exception as e:
        logging.error(f"❌ GET_BLOCKS_LIST (view) test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all query service tests."""
    logging.info("=" * 60)
    logging.info("🚀 Starting Query Services Tests")
    logging.info("=" * 60)
    
    results = []
    
    # Test 1: Get cameras list
    result = await test_get_cameras_list()
    results.append(("GET_CAMERAS_LIST", result))
    
    # Test 2: Get users list
    result = await test_get_users_list()
    results.append(("GET_USERS_LIST", result))
    
    # Test 3: Get blocks list (region query)
    result = await test_get_blocks_list_region()
    results.append(("GET_BLOCKS_LIST (region)", result))
    
    # Test 4: Get blocks list (view query)
    result = await test_get_blocks_list_view()
    results.append(("GET_BLOCKS_LIST (view)", result))
    
    # Summary
    logging.info("")
    logging.info("=" * 60)
    logging.info("📊 TEST SUMMARY")
    logging.info("=" * 60)
    
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logging.info(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logging.info("")
    logging.info(f"Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        logging.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logging.error(f"💥 {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
