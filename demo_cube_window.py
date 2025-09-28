#!/usr/bin/env python3
"""
Demo script showing the cube window abstraction system.
This demonstrates how camera-type cubes can have their own pyglet windows
and provide screenshots through their API endpoints.
"""

import asyncio
import requests
import time
from protocol import Cube
from cube_manager import cube_manager


async def demo_cube_window_system():
    """Demonstrate the cube window abstraction system."""
    print("🎬 Cube Window Abstraction System Demo")
    print("=" * 50)
    
    # Create different types of cubes
    cubes = []
    
    print("\n📦 Creating different types of cubes...")
    
    # 1. Normal cube (no window)
    normal_cube = Cube("normal_cube_1", (10, 50, 10), cube_type="normal", auto_start_server=True)
    normal_cube.port = cube_manager.allocate_port()
    cubes.append(normal_cube)
    
    # 2. Camera cube (with window)
    camera_cube = Cube("camera_cube_1", (20, 50, 20), cube_type="camera", auto_start_server=True)
    camera_cube.port = cube_manager.allocate_port()
    cubes.append(camera_cube)
    
    print(f"   ✅ Normal cube on port {normal_cube.port} (window: {normal_cube.window is not None})")
    print(f"   ✅ Camera cube on port {camera_cube.port} (window: {camera_cube.window is not None})")
    
    # Start servers
    print("\n🚀 Starting cube servers...")
    for cube in cubes:
        await cube.start_server()
        time.sleep(0.5)
    
    try:
        # Demonstrate API usage
        print("\n🔍 Testing cube APIs...")
        
        # Test normal cube
        normal_url = f"http://localhost:{normal_cube.port}"
        print(f"\n1. Normal cube API: {normal_url}")
        response = requests.get(f"{normal_url}/", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"   Type: {info['cube_type']}, Has window: {info['has_window']}")
            
            # Try to get camera image (should fail)
            cam_response = requests.get(f"{normal_url}/camera/image", timeout=5)
            if cam_response.status_code == 200:
                result = cam_response.json()
                print(f"   Camera request result: {result.get('error', 'Success')}")
        
        # Test camera cube
        camera_url = f"http://localhost:{camera_cube.port}"
        print(f"\n2. Camera cube API: {camera_url}")
        response = requests.get(f"{camera_url}/", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"   Type: {info['cube_type']}, Has window: {info['has_window']}")
            
            # Get camera image
            cam_response = requests.get(f"{camera_url}/camera/image", timeout=10)
            if cam_response.status_code == 200 and cam_response.headers.get('content-type') == 'image/png':
                print(f"   📷 Camera image captured: {len(cam_response.content)} bytes")
                
                # Save screenshot
                screenshot_path = f"/tmp/demo_camera_cube_{camera_cube.id}.png"
                with open(screenshot_path, 'wb') as f:
                    f.write(cam_response.content)
                print(f"   💾 Saved to: {screenshot_path}")
        
        # Demonstrate child cube creation
        print(f"\n3. Creating child camera cube...")
        child_response = requests.post(f"{camera_url}/cubes/create", params={
            'child_id': 'child_camera_demo',
            'x': 30.0,
            'y': 50.0,
            'z': 30.0,
            'cube_type': 'camera'
        }, timeout=10)
        
        if child_response.status_code == 200:
            result = child_response.json()
            child_port = result['child_cube']['port']
            print(f"   ✅ Child camera cube created on port {child_port}")
            
            # Test child camera
            child_url = f"http://localhost:{child_port}"
            time.sleep(1)  # Give server time to start
            
            child_info = requests.get(f"{child_url}/", timeout=5)
            if child_info.status_code == 200:
                info = child_info.json()
                print(f"   Child type: {info['cube_type']}, Has window: {info['has_window']}")
                
                # Get child camera image
                child_cam = requests.get(f"{child_url}/camera/image", timeout=10)
                if child_cam.status_code == 200 and child_cam.headers.get('content-type') == 'image/png':
                    child_screenshot_path = f"/tmp/demo_child_camera.png"
                    with open(child_screenshot_path, 'wb') as f:
                        f.write(child_cam.content)
                    print(f"   📷 Child camera image: {len(child_cam.content)} bytes")
                    print(f"   💾 Saved to: {child_screenshot_path}")
        
        # Show API endpoints
        print(f"\n📋 Available API endpoints:")
        print(f"   Normal cube:  {normal_url}")
        print(f"   - GET  /           - Cube info")
        print(f"   - GET  /status     - Cube status")
        print(f"   - POST /move/*     - Movement commands")
        print(f"   - GET  /camera/image - ❌ Not available (not a camera cube)")
        print(f"   ")
        print(f"   Camera cube:  {camera_url}")
        print(f"   - GET  /           - Cube info")
        print(f"   - GET  /status     - Cube status")
        print(f"   - POST /move/*     - Movement commands")
        print(f"   - GET  /camera/image - ✅ Returns PNG screenshot")
        print(f"   - POST /cubes/create - Create child cubes")
        
        print(f"\n🔗 Test the camera endpoints:")
        print(f"   curl {camera_url}/camera/image -o camera_view.png")
        print(f"   curl '{camera_url}/cubes/create?child_id=test&cube_type=camera' -X POST")
        
        print(f"\n⏳ Demo running for 10 seconds...")
        await asyncio.sleep(10)
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for cube in cubes:
            await cube.stop_server()
            if cube.port:
                cube_manager.release_port(cube.port)
        print("   ✅ All cubes stopped and ports released")
    
    print("\n🎉 Demo completed successfully!")


async def main():
    """Run the demo."""
    try:
        await demo_cube_window_system()
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Cube Window Demo")
    print("💡 This demo shows how cubes can have pyglet windows for camera functionality")
    print("⚠️  Run with: DISPLAY=:99 xvfb-run -a python demo_cube_window.py")
    print()
    
    asyncio.run(main())