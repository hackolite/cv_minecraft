#!/usr/bin/env python3
"""
Integration test for the HTTP API endpoints with a running server.
This test verifies that all endpoints work correctly in an integrated environment.
"""

import asyncio
import websockets
import requests
import json
import time
import threading
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8765"

class TestResult:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
    
    def add_result(self, passed: bool):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def print_summary(self):
        print("\n" + "="*60)
        print("Integration Test Summary")
        print("="*60)
        print(f"Tests run:    {self.tests_run}")
        print(f"Tests passed: {self.tests_passed} ✓")
        print(f"Tests failed: {self.tests_failed} ✗")
        print("="*60)
        return self.tests_failed == 0

def test_api_available():
    """Test that the API is available."""
    logger.info("Test: API is available")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'name' in data
        assert 'endpoints' in data
        logger.info("  ✓ PASSED")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_cameras_endpoint():
    """Test the cameras endpoint."""
    logger.info("Test: Cameras endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/api/cameras", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'count' in data
        assert 'cameras' in data
        assert data['count'] > 0  # Should have cameras from world init
        logger.info(f"  ✓ PASSED (found {data['count']} cameras)")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_users_endpoint():
    """Test the users endpoint."""
    logger.info("Test: Users endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/api/users", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'count' in data
        assert 'users' in data
        logger.info(f"  ✓ PASSED (found {data['count']} users)")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_blocks_endpoint():
    """Test the blocks endpoint."""
    logger.info("Test: Blocks endpoint")
    try:
        # Test with valid parameters
        response = requests.get(
            f"{API_BASE_URL}/api/blocks",
            params={'min_x': 60, 'max_x': 70, 'min_y': 95, 'max_y': 105, 'min_z': 60, 'max_z': 70},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert 'count' in data
        assert 'blocks' in data
        assert 'bounds' in data
        logger.info(f"  ✓ PASSED (found {data['count']} blocks)")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_blocks_endpoint_invalid_params():
    """Test the blocks endpoint with invalid parameters."""
    logger.info("Test: Blocks endpoint with invalid params")
    try:
        # Test with invalid parameters (should return 400)
        response = requests.get(
            f"{API_BASE_URL}/api/blocks",
            params={'min_x': -10, 'max_x': 200},
            timeout=5
        )
        assert response.status_code == 400
        logger.info("  ✓ PASSED (correctly rejected invalid params)")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_render_endpoint():
    """Test the render endpoint."""
    logger.info("Test: Render endpoint")
    try:
        payload = {
            'position': [64.0, 100.0, 64.0],
            'rotation': [0.0, 0.0],
            'width': 640,
            'height': 480
        }
        response = requests.post(f"{API_BASE_URL}/api/render", json=payload, timeout=10)
        assert response.status_code == 200
        assert 'image/png' in response.headers.get('content-type', '')
        assert len(response.content) > 0
        logger.info(f"  ✓ PASSED (rendered {len(response.content)} bytes)")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_render_endpoint_invalid_params():
    """Test the render endpoint with invalid parameters."""
    logger.info("Test: Render endpoint with invalid params")
    try:
        # Test with invalid position (should return 400)
        payload = {
            'position': [64.0, 100.0],  # Only 2 coordinates instead of 3
            'rotation': [0.0, 0.0]
        }
        response = requests.post(f"{API_BASE_URL}/api/render", json=payload, timeout=10)
        assert response.status_code == 400
        logger.info("  ✓ PASSED (correctly rejected invalid params)")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

async def test_with_websocket_client():
    """Test API with a connected WebSocket client."""
    logger.info("Test: API with connected WebSocket client")
    try:
        async with websockets.connect(WS_URL) as ws:
            # Join as a player
            join_msg = {"type": "player_join", "data": {"name": "APITestPlayer"}}
            await ws.send(json.dumps(join_msg))
            
            # Wait for world init
            await asyncio.wait_for(ws.recv(), timeout=5.0)
            
            # Wait a bit for server to register the player
            await asyncio.sleep(0.5)
            
            # Now test the users endpoint
            response = requests.get(f"{API_BASE_URL}/api/users", timeout=5)
            assert response.status_code == 200
            data = response.json()
            
            # Should have at least 1 user now
            assert data['count'] >= 1
            
            # Check if our player is in the list
            player_names = [u['name'] for u in data['users']]
            assert 'APITestPlayer' in player_names
            
            logger.info("  ✓ PASSED (WebSocket client visible in API)")
            return True
            
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_openapi_schema():
    """Test that OpenAPI schema is available."""
    logger.info("Test: OpenAPI schema")
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=5)
        assert response.status_code == 200
        schema = response.json()
        assert 'openapi' in schema
        assert 'paths' in schema
        assert '/api/cameras' in schema['paths']
        assert '/api/users' in schema['paths']
        assert '/api/blocks' in schema['paths']
        assert '/api/render' in schema['paths']
        logger.info("  ✓ PASSED")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

def test_swagger_ui():
    """Test that Swagger UI is available."""
    logger.info("Test: Swagger UI")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        assert response.status_code == 200
        assert 'swagger-ui' in response.text.lower()
        logger.info("  ✓ PASSED")
        return True
    except Exception as e:
        logger.error(f"  ✗ FAILED: {e}")
        return False

async def run_async_tests():
    """Run async tests."""
    result = TestResult()
    
    # Test with WebSocket client
    result.add_result(await test_with_websocket_client())
    
    return result

def run_sync_tests():
    """Run synchronous tests."""
    result = TestResult()
    
    # Basic API tests
    result.add_result(test_api_available())
    result.add_result(test_cameras_endpoint())
    result.add_result(test_users_endpoint())
    result.add_result(test_blocks_endpoint())
    result.add_result(test_blocks_endpoint_invalid_params())
    result.add_result(test_render_endpoint())
    result.add_result(test_render_endpoint_invalid_params())
    result.add_result(test_openapi_schema())
    result.add_result(test_swagger_ui())
    
    return result

def main():
    """Run all integration tests."""
    print("="*60)
    print("HTTP API Integration Tests")
    print("="*60)
    print()
    
    # Check if server is available
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        logger.info(f"✓ Server is available at {API_BASE_URL}")
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Server is not available at {API_BASE_URL}")
        logger.error("Please start the server with: python3 server.py")
        return 1
    
    print()
    logger.info("Running synchronous tests...")
    print()
    
    sync_result = run_sync_tests()
    
    print()
    logger.info("Running asynchronous tests...")
    print()
    
    async_result = asyncio.run(run_async_tests())
    
    # Combine results
    total_result = TestResult()
    total_result.tests_run = sync_result.tests_run + async_result.tests_run
    total_result.tests_passed = sync_result.tests_passed + async_result.tests_passed
    total_result.tests_failed = sync_result.tests_failed + async_result.tests_failed
    
    success = total_result.print_summary()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
