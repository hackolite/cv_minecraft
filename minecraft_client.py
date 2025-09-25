#!/usr/bin/env python3
"""
Minecraft Client Abstracted - Classe Client Abstraite
====================================================

Cette classe abstrait le code de minecraft_client_fr.py pour permettre:
- Un client utilisable par un humain pour jouer
- Un serveur FastAPI intégré pour contrôler le client via des endpoints
- Support pour position, type de bloc configurables
- Présentation de ce que voit l'utilisateur

Usage:
    from minecraft_client import MinecraftClient
    
    client = MinecraftClient(position=[30, 50, 80], block_type="GRASS")
    client.start_server()  # Démarre le serveur FastAPI
    client.run()  # Démarre le client graphique
"""

import sys
import math
import threading
import asyncio
import time
from typing import Optional, Tuple, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import io
import base64

# Import the original client components
try:
    from minecraft_client_fr import (
        MinecraftWindow, EnhancedClientModel, AdvancedNetworkClient,
        BlockType, setup_opengl, config
    )
    import pyglet
    from pyglet.gl import *
    from PIL import Image
    HAS_DISPLAY = True
except ImportError as e:
    print(f"Warning: Display/GUI components not available: {e}")
    HAS_DISPLAY = False
    # Create dummy classes for headless mode
    class MinecraftWindow:
        def __init__(self):
            self.position = (30, 50, 80)
            self.rotation = (0, 0)
            self.flying = False
            
    class EnhancedClientModel:
        def __init__(self):
            self.world = {}
            self.shown = {}
            
        def add_block(self, position, block_type):
            self.world[position] = block_type
            
        def remove_block(self, position):
            if position in self.world:
                del self.world[position]
    
    class BlockType:
        GRASS = "GRASS"
        STONE = "STONE"
        SAND = "SAND"
        BRICK = "BRICK"
    
    def setup_opengl():
        pass


class MinecraftClient:
    """
    Classe client Minecraft abstraite avec serveur FastAPI intégré.
    
    Cette classe permet de contrôler un client Minecraft soit:
    - Directement via l'interface graphique (pour les humains)
    - Via des endpoints FastAPI (pour le contrôle programmatique)
    """
    
    def __init__(self, 
                 position: Optional[Tuple[float, float, float]] = None,
                 block_type: str = "GRASS",
                 server_host: str = "localhost",
                 server_port: int = 8080,
                 enable_gui: bool = True):
        """
        Initialise le client Minecraft.
        
        Args:
            position: Position initiale (x, y, z) du joueur
            block_type: Type de bloc par défaut 
            server_host: Host du serveur FastAPI
            server_port: Port du serveur FastAPI
            enable_gui: Active/désactive l'interface graphique
        """
        self.server_host = server_host
        self.server_port = server_port
        self.enable_gui = enable_gui
        
        # Position initiale
        if position:
            config.set("player", "preferred_spawn", list(position))
        
        # Configuration du bloc par défaut
        self.default_block_type = getattr(BlockType, block_type.upper(), BlockType.GRASS)
        
        # État du client
        self.window = None
        self.running = False
        self.server_thread = None
        
        # Serveur FastAPI
        self.app = FastAPI(
            title="Minecraft Client Controller",
            description="API pour contrôler le client Minecraft"
        )
        self._setup_api_routes()
        
    def _setup_api_routes(self):
        """Configure les routes de l'API FastAPI."""
        
        @self.app.get("/")
        async def home():
            """Page d'accueil de l'API."""
            return {
                "message": "Minecraft Client Controller API",
                "status": "running" if self.running else "stopped",
                "position": self.get_position() if self.window else None,
                "endpoints": {
                    "move": "/move",
                    "teleport": "/teleport", 
                    "place_block": "/place_block",
                    "remove_block": "/remove_block",
                    "get_view": "/get_view",
                    "get_status": "/status"
                }
            }
        
        @self.app.post("/move")
        async def move(dx: float = 0, dy: float = 0, dz: float = 0):
            """Déplace le joueur de façon relative."""
            if not self.window:
                raise HTTPException(status_code=400, detail="Client not running")
            
            current_pos = self.window.position
            new_pos = (current_pos[0] + dx, current_pos[1] + dy, current_pos[2] + dz)
            self._set_position(new_pos)
            
            return {
                "message": "Player moved",
                "previous_position": current_pos,
                "new_position": new_pos
            }
        
        @self.app.post("/teleport")
        async def teleport(x: float, y: float, z: float):
            """Téléporte le joueur à une position absolue."""
            if not self.window:
                raise HTTPException(status_code=400, detail="Client not running")
            
            new_pos = (x, y, z)
            self._set_position(new_pos)
            
            return {
                "message": "Player teleported",
                "position": new_pos
            }
        
        @self.app.post("/place_block")
        async def place_block(x: int, y: int, z: int, block_type: str = None):
            """Place un bloc à la position spécifiée."""
            if not self.window:
                raise HTTPException(status_code=400, detail="Client not running")
            
            if block_type:
                try:
                    block = getattr(BlockType, block_type.upper())
                except AttributeError:
                    raise HTTPException(status_code=400, detail=f"Invalid block type: {block_type}")
            else:
                block = self.default_block_type
            
            position = (x, y, z)
            self.window.model.add_block(position, block)
            
            return {
                "message": "Block placed",
                "position": position,
                "block_type": block_type or self.default_block_type.name
            }
        
        @self.app.post("/remove_block")
        async def remove_block(x: int, y: int, z: int):
            """Supprime un bloc à la position spécifiée."""
            if not self.window:
                raise HTTPException(status_code=400, detail="Client not running")
            
            position = (x, y, z)
            self.window.model.remove_block(position)
            
            return {
                "message": "Block removed",
                "position": position
            }
        
        @self.app.get("/get_view")
        async def get_view():
            """Récupère une capture d'écran de ce que voit le joueur."""
            if not self.window or not HAS_DISPLAY:
                raise HTTPException(status_code=400, detail="Client not running or display not available")
            
            try:
                # Capture de l'écran
                screenshot = self._take_screenshot()
                if screenshot:
                    return StreamingResponse(
                        io.BytesIO(screenshot),
                        media_type="image/png"
                    )
                else:
                    raise HTTPException(status_code=500, detail="Failed to capture screenshot")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Screenshot error: {str(e)}")
        
        @self.app.get("/status")
        async def get_status():
            """Récupère le statut complet du client."""
            if not self.window:
                return {
                    "running": False,
                    "gui_enabled": self.enable_gui
                }
            
            return {
                "running": self.running,
                "gui_enabled": self.enable_gui,
                "position": self.get_position(),
                "rotation": self.window.rotation,
                "flying": self.window.flying,
                "block_type": self.default_block_type.name,
                "world_blocks": len(self.window.model.world),
                "visible_blocks": len(self.window.model.shown)
            }
    
    def _set_position(self, position: Tuple[float, float, float]):
        """Définit la position du joueur (thread-safe)."""
        if self.window:
            # Schedule position update on main thread
            pyglet.clock.schedule_once(lambda dt: setattr(self.window, 'position', position), 0)
    
    def _take_screenshot(self) -> Optional[bytes]:
        """Prend une capture d'écran de la fenêtre."""
        if not self.window or not HAS_DISPLAY:
            return None
        
        try:
            # Force a redraw
            self.window.dispatch_event('on_draw')
            
            # Read pixels from framebuffer
            width, height = self.window.get_size()
            pixels = (GLubyte * (3 * width * height))(0)
            glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, pixels)
            
            # Convert to PIL Image and flip vertically
            image = Image.frombytes('RGB', (width, height), pixels)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            
            # Convert to PNG bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None
    
    def get_position(self) -> Optional[Tuple[float, float, float]]:
        """Récupère la position actuelle du joueur."""
        return self.window.position if self.window else None
    
    def start_server(self) -> bool:
        """Démarre le serveur FastAPI dans un thread séparé."""
        if self.server_thread and self.server_thread.is_alive():
            print("Server already running")
            return True
        
        def run_server():
            try:
                uvicorn.run(self.app, host=self.server_host, port=self.server_port, log_level="info")
            except Exception as e:
                print(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait a bit to ensure server starts
        time.sleep(2)
        
        print(f"🚀 FastAPI server started on http://{self.server_host}:{self.server_port}")
        print(f"📊 API documentation: http://{self.server_host}:{self.server_port}/docs")
        
        return True
    
    def run(self):
        """Lance le client Minecraft."""
        if not HAS_DISPLAY and self.enable_gui:
            print("Warning: Display not available, GUI disabled")
            self.enable_gui = False
        
        if self.enable_gui:
            try:
                print("🎮 Starting Minecraft Client...")
                self.window = MinecraftWindow()
                
                # Set default block type
                if hasattr(self.window, 'block'):
                    self.window.block = self.default_block_type
                
                setup_opengl()
                self.running = True
                
                print("✅ Client started successfully!")
                print(f"🎯 Starting position: {self.window.position}")
                print(f"🧱 Default block: {getattr(self.default_block_type, 'name', self.default_block_type)}")
                
                if self.server_thread and self.server_thread.is_alive():
                    print(f"🌐 API available at: http://{self.server_host}:{self.server_port}")
                
                pyglet.app.run()
                
            except Exception as e:
                print(f"❌ Client error: {e}")
                raise
            finally:
                self.running = False
        else:
            # Headless mode - create a minimal window object for API compatibility
            print("🔧 Running in headless mode (server only)")
            self.window = MinecraftWindow()  # Create dummy window
            self.running = True
            
            print("✅ Headless client started successfully!")
            print(f"🎯 Starting position: {self.window.position}")
            print(f"🧱 Default block: {getattr(self.default_block_type, 'name', self.default_block_type)}")
            
            if self.server_thread and self.server_thread.is_alive():
                print(f"🌐 API available at: http://{self.server_host}:{self.server_port}")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Server stopped by user")
            finally:
                self.running = False


def main():
    """Point d'entrée principal pour tester la classe client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Minecraft Client with FastAPI integration")
    parser.add_argument('--position', nargs=3, type=float, default=[30, 50, 80],
                       help='Starting position [x y z]')
    parser.add_argument('--block-type', default='GRASS', 
                       help='Default block type')
    parser.add_argument('--server-host', default='localhost',
                       help='FastAPI server host')
    parser.add_argument('--server-port', type=int, default=8080,
                       help='FastAPI server port')
    parser.add_argument('--headless', action='store_true',
                       help='Run without GUI (server only)')
    
    args = parser.parse_args()
    
    # Create and configure client
    client = MinecraftClient(
        position=tuple(args.position),
        block_type=args.block_type,
        server_host=args.server_host,
        server_port=args.server_port,
        enable_gui=not args.headless
    )
    
    # Start server
    client.start_server()
    
    # Run client
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n👋 Client stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())