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
    print("  2. Enable movement and control capabilities")
    print("  3. Allow creation of child cubes programmatically")
    print()
    print("Server will run on ws://localhost:8765")
    print()
    print("To test:")
    print("  1. Connect a WebSocket client to ws://localhost:8765")
    print("  2. Check server logs for user cube creation")
    print("  3. Use game controls or programmatic methods to control your cube")
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