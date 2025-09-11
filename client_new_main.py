#!/usr/bin/env python3
"""
New client entry point using pyCraft-inspired architecture
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client_new.game_client import GameClient


async def main():
    """Main entry point for the new client"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Get username from command line or use default
    username = sys.argv[1] if len(sys.argv) > 1 else "Player"
    
    logger.info(f"Starting new Minecraft-like client for {username}")
    logger.info("Using pyCraft-inspired architecture with packet-based protocol")
    
    # Create and start game client
    client = GameClient(username=username, render_enabled=True)
    
    try:
        # Start client (this will handle connection, rendering, etc.)
        success = await client.start(host="localhost", port=8766)
        
        if not success:
            logger.error("Failed to start client")
            return
        
        # Keep client running
        logger.info("Client started successfully. Press Ctrl+C to quit.")
        
        # Wait for client to stop (user closes window or presses Ctrl+C)
        while client.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        # Clean shutdown
        await client.stop()
        logger.info("Client stopped")


if __name__ == "__main__":
    asyncio.run(main())