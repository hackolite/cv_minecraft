#!/usr/bin/env python3
"""
Simple demo to show cube API functionality
"""

import asyncio
import requests
import time
from protocol import Cube
from cube_manager import cube_manager

async def demo_cube_api():
    """Demonstrate cube API endpoints."""
    print("🎯 Cube API Demo")
    print("=" * 50)
    
    # Create and start a cube
    cube = Cube("demo_cube", (100, 50, 100), base_url="localhost")
    cube.port = cube_manager.allocate_port()
    
    if not cube.port:
        print("❌ Could not allocate port")
        return
    
    cube.setup_fastapi_server()
    await cube.start_server()
    
    print(f"🚀 Demo cube started on http://localhost:{cube.port}")
    print(f"📋 Available endpoints at http://localhost:{cube.port}/docs")
    print()
    
    try:
        base_url = f"http://localhost:{cube.port}"
        
        # Test info endpoint
        print("1. Getting cube information:")
        response = requests.get(f"{base_url}/", timeout=2)
        if response.status_code == 200:
            info = response.json()
            print(f"   ✅ Cube ID: {info['cube_id']}")
            print(f"   ✅ Position: {info['position']}")
            print(f"   ✅ Status: {info['status']}")
        
        print()
        
        # Test movement
        print("2. Testing movement:")
        movements = [
            ("forward", 5),
            ("right", 3), 
            ("back", 2),
            ("left", 1)
        ]
        
        for direction, distance in movements:
            response = requests.post(f"{base_url}/move/{direction}?distance={distance}", timeout=2)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {direction.capitalize()} {distance}: {result['position']}")
        
        print()
        
        # Test jump
        print("3. Testing jump:")
        response = requests.post(f"{base_url}/move/jump?height=3", timeout=2)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Jump: {result['position']}")
        
        print()
        
        # Test camera rotation
        print("4. Testing camera rotation:")
        response = requests.post(f"{base_url}/camera/rotate?horizontal=45&vertical=10", timeout=2)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Camera rotated: {result['rotation']}")
        
        print()
        
        # Test child cube creation
        print("5. Testing child cube creation:")
        response = requests.post(f"{base_url}/cubes/create?child_id=demo_child&x=110&y=50&z=110", timeout=5)
        if response.status_code == 200:
            result = response.json()
            child_port = result['child_cube']['port']
            print(f"   ✅ Child cube created on port {child_port}")
            
            # Test child cube API
            child_response = requests.get(f"http://localhost:{child_port}/", timeout=2)
            if child_response.status_code == 200:
                child_info = child_response.json()
                print(f"   ✅ Child cube accessible: {child_info['cube_id']}")
        
        # List child cubes
        response = requests.get(f"{base_url}/cubes", timeout=2)
        if response.status_code == 200:
            cubes = response.json()
            print(f"   ✅ Child cubes: {len(cubes['child_cubes'])}")
        
        print()
        print("🎉 All API endpoints working correctly!")
        print()
        print("You can now test manually with:")
        print(f"  curl {base_url}/")
        print(f"  curl -X POST {base_url}/move/forward?distance=10")
        print(f"  curl -X POST '{base_url}/cubes/create?child_id=manual_child&x=120&y=50&z=120'")
        print()
        print("Press Enter to stop the demo...")
        input()
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    finally:
        # Cleanup
        await cube.stop_server()
        cube_manager.release_port(cube.port)
        print("✅ Demo cube cleaned up")

if __name__ == "__main__":
    asyncio.run(demo_cube_api())