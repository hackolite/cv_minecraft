#!/usr/bin/env python3
"""
Test script for the new HTTP API endpoints.
"""

import asyncio
import time
import requests
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"

def test_api_home():
    """Test the API home endpoint."""
    logger.info("Testing API home endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API Home: {data}")
            return True
        else:
            logger.error(f"❌ API Home failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ API Home error: {e}")
        return False

def test_cameras_endpoint():
    """Test the /api/cameras endpoint."""
    logger.info("Testing /api/cameras endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/cameras", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Cameras: Found {data['count']} cameras")
            for cam in data['cameras'][:3]:  # Show first 3
                logger.info(f"   Camera at {cam['position']}")
            return True
        else:
            logger.error(f"❌ Cameras endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cameras endpoint error: {e}")
        return False

def test_users_endpoint():
    """Test the /api/users endpoint."""
    logger.info("Testing /api/users endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/users", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Users: Found {data['count']} users")
            for user in data['users'][:3]:  # Show first 3
                logger.info(f"   User {user['name']} at {user['position']}")
            return True
        else:
            logger.error(f"❌ Users endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Users endpoint error: {e}")
        return False

def test_blocks_endpoint():
    """Test the /api/blocks endpoint."""
    logger.info("Testing /api/blocks endpoint...")
    try:
        # Test with a small area around spawn
        params = {
            "min_x": 60,
            "min_y": 95,
            "min_z": 60,
            "max_x": 70,
            "max_y": 105,
            "max_z": 70
        }
        response = requests.get(f"{API_BASE_URL}/api/blocks", params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Blocks: Found {data['count']} blocks in area")
            logger.info(f"   Bounds: {data['bounds']}")
            return True
        else:
            logger.error(f"❌ Blocks endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Blocks endpoint error: {e}")
        return False

def test_render_endpoint():
    """Test the /api/render endpoint."""
    logger.info("Testing /api/render endpoint...")
    try:
        # Render from spawn position
        payload = {
            "position": [64.0, 100.0, 64.0],
            "rotation": [0.0, 0.0],
            "width": 640,
            "height": 480,
            "fov": 65.0,
            "render_distance": 30
        }
        response = requests.post(f"{API_BASE_URL}/api/render", json=payload, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image/png' in content_type:
                logger.info(f"✅ Render: Received PNG image ({len(response.content)} bytes)")
                
                # Save the image to verify
                with open('/tmp/test_render.png', 'wb') as f:
                    f.write(response.content)
                logger.info(f"   Saved to /tmp/test_render.png")
                return True
            else:
                logger.error(f"❌ Render returned wrong content type: {content_type}")
                return False
        else:
            logger.error(f"❌ Render endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Render endpoint error: {e}")
        return False

def main():
    """Run all API tests."""
    logger.info("=" * 60)
    logger.info("Testing Minecraft Server HTTP API Endpoints")
    logger.info("=" * 60)
    
    # Wait a bit for server to be ready
    logger.info("Waiting for server to be ready...")
    time.sleep(2)
    
    results = {
        "API Home": test_api_home(),
        "Cameras": test_cameras_endpoint(),
        "Users": test_users_endpoint(),
        "Blocks": test_blocks_endpoint(),
        "Render": test_render_endpoint()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:20} : {status}")
    
    logger.info("=" * 60)
    logger.info(f"Overall: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
