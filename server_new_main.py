#!/usr/bin/env python3
"""
New server entry point using pyCraft-inspired architecture
"""

import asyncio
import logging
import sys
import os
import signal

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server_new.network_server import NetworkServer


class MinecraftServer:
    """Main server class"""
    
    def __init__(self, host: str = "localhost", port: int = 8766):
        self.network_server = NetworkServer(host, port)
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start(self):
        """Start the server"""
        self.logger.info("Starting Minecraft-like server")
        self.logger.info("Using pyCraft-inspired architecture with packet-based protocol")
        
        try:
            self.running = True
            
            # Start network server
            await self.network_server.start()
            
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the server"""
        if not self.running:
            return
        
        self.logger.info("Stopping server...")
        self.running = False
        
        # Stop network server
        await self.network_server.stop()
        
        self.logger.info("Server stopped")
    
    def get_stats(self):
        """Get server statistics"""
        return self.network_server.get_stats()


async def main():
    """Main entry point"""
    # Parse command line arguments
    host = "localhost"
    port = 8766
    
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port: {sys.argv[2]}")
            return
    
    # Create and start server
    server = MinecraftServer(host, port)
    
    print(f"""
🎮 Minecraft-like Server (pyCraft-inspired Architecture)
==================================================

Server Configuration:
• Host: {host}
• Port: {port}
• Protocol: TCP with binary packets
• Architecture: Modular (Network/World/Player managers)

Features:
• Packet-based protocol inspired by pyCraft
• Proper authentication and session management
• Separated concerns (networking, world, players)
• Binary packet serialization
• Connection health monitoring

Starting server...
""")
    
    try:
        await server.start()
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())