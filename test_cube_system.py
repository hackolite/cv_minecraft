#!/usr/bin/env python3
"""
Test script for the cube abstraction system
"""

import asyncio
import time
from protocol import Cube
from cube_manager import cube_manager

async def test_cube_creation():
    """Test creating a cube with FastAPI server."""
    print("🧪 Testing Cube Creation and FastAPI Server")
    print("=" * 50)
    
    # Create a cube
    cube = Cube("test_cube_1", (10, 50, 10), base_url="localhost")
    
    # Allocate port and setup server
    cube.port = cube_manager.allocate_port()
    print(f"✅ Allocated port: {cube.port}")
    
    if cube.port:
        cube.setup_fastapi_server()
        await cube.start_server()
        print(f"✅ Cube server started on http://localhost:{cube.port}")
        
        # Test basic API endpoints
        import requests
        try:
            # Test info endpoint
            response = requests.get(f"http://localhost:{cube.port}/", timeout=2)
            if response.status_code == 200:
                print("✅ Info endpoint working")
                print(f"   Response: {response.json()}")
            
            # Test status endpoint
            response = requests.get(f"http://localhost:{cube.port}/status", timeout=2)
            if response.status_code == 200:
                print("✅ Status endpoint working")
                print(f"   Response: {response.json()}")
            
            # Test movement endpoint
            response = requests.post(f"http://localhost:{cube.port}/move/forward?distance=5", timeout=2)
            if response.status_code == 200:
                print("✅ Movement endpoint working")
                print(f"   Response: {response.json()}")
                print(f"   New position: {cube.position}")
                
        except Exception as e:
            print(f"❌ API test failed: {e}")
        
        # Clean up
        await cube.stop_server()
        cube_manager.release_port(cube.port)
        print("✅ Cube server stopped and port released")
    
    print("✅ Cube creation test completed")

async def test_child_cube_creation():
    """Test creating child cubes."""
    print("\n🧪 Testing Child Cube Creation")
    print("=" * 50)
    
    # Create parent cube
    parent_cube = Cube("parent_cube", (0, 50, 0), base_url="localhost")
    parent_cube.port = cube_manager.allocate_port()
    
    if parent_cube.port:
        parent_cube.setup_fastapi_server()
        await parent_cube.start_server()
        print(f"✅ Parent cube server started on http://localhost:{parent_cube.port}")
        
        try:
            # Test child cube creation via API
            import requests
            response = requests.post(
                f"http://localhost:{parent_cube.port}/cubes/create?child_id=child1&x=5&y=50&z=5", 
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Child cube creation API working")
                print(f"   Response: {response.json()}")
                
                # List child cubes
                response = requests.get(f"http://localhost:{parent_cube.port}/cubes", timeout=2)
                if response.status_code == 200:
                    print("✅ Child cube listing working")
                    print(f"   Response: {response.json()}")
                
        except Exception as e:
            print(f"❌ Child cube test failed: {e}")
        
        # Clean up
        await parent_cube.stop_server()
        cube_manager.release_port(parent_cube.port)
        print("✅ Parent cube cleaned up")
    
    print("✅ Child cube creation test completed")

async def test_port_management():
    """Test port allocation and release."""
    print("\n🧪 Testing Port Management")
    print("=" * 50)
    
    print(f"Available ports before: {cube_manager.get_available_port_count()}")
    
    # Allocate several ports
    ports = []
    for i in range(5):
        port = cube_manager.allocate_port()
        if port:
            ports.append(port)
            print(f"✅ Allocated port {port}")
        else:
            print("❌ Failed to allocate port")
    
    print(f"Available ports after allocation: {cube_manager.get_available_port_count()}")
    print(f"Used ports: {cube_manager.get_used_ports()}")
    
    # Release ports
    for port in ports:
        cube_manager.release_port(port)
        print(f"✅ Released port {port}")
    
    print(f"Available ports after release: {cube_manager.get_available_port_count()}")
    print("✅ Port management test completed")

async def main():
    """Main test function."""
    print("🚀 Starting Cube System Tests")
    print("=" * 60)
    
    try:
        await test_port_management()
        await test_cube_creation()
        await test_child_cube_creation()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())