#!/usr/bin/env python3
"""
Test script for cube window abstraction system.
Tests the creation of camera-type cubes and image capture functionality.
"""

import asyncio
import requests
import time
from protocol import Cube
from cube_manager import cube_manager


def test_cube_window_creation():
    """Test creating cubes with different types including camera type."""
    print("🧪 Testing Cube Window Creation")
    print("=" * 50)
    
    # Test 1: Create a normal cube (should not have window)
    print("\n1. Creating normal cube...")
    normal_cube = Cube("normal_cube_1", (10, 50, 10), cube_type="normal")
    print(f"   Normal cube has window: {normal_cube.window is not None}")
    assert normal_cube.window is None, "Normal cube should not have a window"
    print("   ✅ Normal cube created correctly (no window)")
    
    # Test 2: Create a camera cube (should have window)
    print("\n2. Creating camera cube...")
    camera_cube = Cube("camera_cube_1", (20, 50, 20), cube_type="camera")
    print(f"   Camera cube has window: {camera_cube.window is not None}")
    assert camera_cube.window is not None, "Camera cube should have a window"
    print("   ✅ Camera cube created correctly (with window)")
    
    # Test 3: Test window screenshot functionality
    print("\n3. Testing camera cube screenshot...")
    if camera_cube.window:
        try:
            screenshot_bytes = camera_cube.window.take_screenshot()
            if screenshot_bytes:
                print(f"   Screenshot captured: {len(screenshot_bytes)} bytes")
                print("   ✅ Screenshot functionality works")
            else:
                print("   ⚠️  Screenshot returned None")
        except Exception as e:
            print(f"   ⚠️  Screenshot failed: {e}")
    
    # Cleanup
    print("\n4. Cleaning up...")
    if camera_cube.window:
        camera_cube.window.close()
        print("   ✅ Camera cube window closed")
    
    print("\n🎉 Cube window creation test completed!")


async def test_cube_api_with_camera():
    """Test the API functionality with camera cubes."""
    print("\n🧪 Testing Cube API with Camera Support")
    print("=" * 50)
    
    # Create and start a camera cube server
    camera_cube = Cube("api_camera_cube", (30, 50, 30), cube_type="camera", auto_start_server=True)
    
    # Allocate port
    camera_cube.port = cube_manager.allocate_port()
    if not camera_cube.port:
        print("❌ Failed to allocate port")
        return
    
    print(f"✅ Allocated port: {camera_cube.port}")
    
    try:
        # Start the server
        await camera_cube.start_server()
        time.sleep(2)  # Give server time to start
        
        base_url = f"http://localhost:{camera_cube.port}"
        
        # Test 1: Get cube info
        print(f"\n1. Testing info endpoint: GET {base_url}/")
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                info = response.json()
                print(f"   Cube type: {info.get('cube_type')}")
                print(f"   Has window: {info.get('has_window')}")
                print("   ✅ Info endpoint works")
            else:
                print(f"   ❌ Info endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Info endpoint error: {e}")
        
        # Test 2: Try to get camera image
        print(f"\n2. Testing camera image endpoint: GET {base_url}/camera/image")
        try:
            response = requests.get(f"{base_url}/camera/image", timeout=10)
            if response.status_code == 200:
                if response.headers.get('content-type') == 'image/png':
                    print(f"   ✅ Camera image captured: {len(response.content)} bytes")
                    # Save image for verification
                    with open('/tmp/test_camera_cube_image.png', 'wb') as f:
                        f.write(response.content)
                    print("   📷 Image saved to /tmp/test_camera_cube_image.png")
                else:
                    result = response.json()
                    print(f"   ⚠️  Non-image response: {result}")
            else:
                print(f"   ❌ Camera image failed: {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error details: {error}")
                except:
                    print(f"   Error text: {response.text}")
        except Exception as e:
            print(f"   ❌ Camera image error: {e}")
        
        # Test 3: Create a child camera cube
        print(f"\n3. Testing child camera creation: POST {base_url}/cubes/create")
        try:
            response = requests.post(f"{base_url}/cubes/create", params={
                'child_id': 'child_camera_1',
                'x': 40.0,
                'y': 50.0,
                'z': 40.0,
                'cube_type': 'camera'
            }, timeout=10)
            if response.status_code == 200:
                result = response.json()
                child_port = result['child_cube']['port']
                print(f"   ✅ Child camera cube created on port {child_port}")
                
                # Test child camera image
                child_url = f"http://localhost:{child_port}"
                print(f"   Testing child camera: GET {child_url}/camera/image")
                time.sleep(1)  # Give child server time to start
                
                child_response = requests.get(f"{child_url}/camera/image", timeout=10)
                if child_response.status_code == 200 and child_response.headers.get('content-type') == 'image/png':
                    print(f"   ✅ Child camera image: {len(child_response.content)} bytes")
                else:
                    print(f"   ⚠️  Child camera image failed: {child_response.status_code}")
            else:
                print(f"   ❌ Child creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Child creation error: {e}")
        
    finally:
        # Cleanup
        print(f"\n4. Cleaning up...")
        await camera_cube.stop_server()
        cube_manager.release_port(camera_cube.port)
        print("   ✅ Server stopped and port released")
    
    print("\n🎉 Cube API camera test completed!")


async def main():
    """Run all tests."""
    print("🚀 Starting Cube Window Abstraction Tests")
    print("=" * 60)
    
    # Test 1: Basic window creation
    test_cube_window_creation()
    
    # Test 2: API integration
    await test_cube_api_with_camera()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())