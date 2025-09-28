#!/usr/bin/env python3
"""
Demo script showing the cube abstraction system with user connections
"""

import asyncio
import logging
from server import MinecraftServer

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Demo of the cube server system."""
    print("🚀 Starting Minecraft Server with Cube Abstraction")
    print("=" * 60)
    print()
    print("Each user connection will:")
    print("  1. Create a Cube object representing the user")
    print("  2. Allocate a dedicated port for the cube's FastAPI server")
    print("  3. Start a FastAPI server with movement and control endpoints")
    print("  4. Allow creation of child cubes via the API")
    print()
    print("Available endpoints for each user cube:")
    print("  GET  /              - Cube information")
    print("  GET  /status        - Status and color")
    print("  POST /move/forward  - Move forward")
    print("  POST /move/back     - Move backward")
    print("  POST /move/left     - Move left")
    print("  POST /move/right    - Move right")
    print("  POST /move/jump     - Jump")
    print("  POST /camera/rotate - Rotate camera")
    print("  GET  /camera/image  - Get camera image")
    print("  POST /cubes/create  - Create child cube")
    print("  DELETE /cubes/{id}  - Destroy child cube")
    print("  GET  /cubes         - List child cubes")
    print()
    print("Server will run on ws://localhost:8765")
    print("Individual cube APIs will use ports 8081+")
    print()
    print("To test:")
    print("  1. Connect a WebSocket client to ws://localhost:8765")
    print("  2. Check server logs for allocated cube port")
    print("  3. Use HTTP requests to control your cube")
    print()
    print("Example cube control:")
    print("  curl http://localhost:8081/")
    print("  curl -X POST http://localhost:8081/move/forward?distance=5")
    print("  curl -X POST 'http://localhost:8081/cubes/create?child_id=child1&x=10&y=50&z=10'")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    server = MinecraftServer()
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.stop_server()
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())