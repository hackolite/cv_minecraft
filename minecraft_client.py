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
        BlockType, setup_opengl
    )
    from client_config import config
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
            self.model = EnhancedClientModel()  # Add missing model attribute
            
        def get_size(self):
            """Dummy method for headless compatibility."""
            return (800, 600)
            
        def dispatch_event(self, event_type):
            """Dummy method for headless compatibility."""
            pass
            
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
        CAMERA = "CAMERA"
    
    def setup_opengl():
        pass
    
    # Dummy config for headless mode
    class DummyConfig:
        def set(self, section, key, value):
            pass
        def get(self, section, key, default=None):
            return default
    config = DummyConfig()


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
                 enable_gui: bool = True,
                 auto_capture: bool = True,
                 capture_interval: float = 0.1):
        """
        Initialise le client Minecraft avec capture d'images automatique.
        
        Args:
            position: Position initiale (x, y, z) du joueur
            block_type: Type de bloc par défaut 
            server_host: Host du serveur FastAPI
            server_port: Port du serveur FastAPI
            enable_gui: Active/désactive l'interface graphique
            auto_capture: Active la capture automatique d'images (inspiré de mini_minecraft_pyglet_server)
            capture_interval: Intervalle entre les captures en secondes
        """
        self.server_host = server_host
        self.server_port = server_port
        self.enable_gui = enable_gui
        self.auto_capture = auto_capture
        self.capture_interval = capture_interval
        
        # Position initiale
        if position:
            config.set("player", "preferred_spawn", list(position))
        
        # Configuration du bloc par défaut
        self.default_block_type = getattr(BlockType, block_type.upper(), BlockType.GRASS)
        
        # État du client
        self.window = None
        self.running = False
        self.app_running = False  # Track if pyglet app is running
        self.server_thread = None
        
        # Variables pour la capture d'images automatique (inspirées de mini_minecraft_pyglet_server_corrected.py)
        self.latest_image = None
        self.image_lock = threading.Lock()
        
        # Serveur FastAPI
        self.app = FastAPI(
            title="Minecraft Client Controller",
            description="API pour contrôler le client Minecraft avec capture d'images"
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
                    "view": "/view",
                    "get_status": "/status"
                },
                "auto_capture": self.auto_capture,
                "capture_interval": self.capture_interval if self.auto_capture else None
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
        
        @self.app.get("/view")
        async def get_cached_view():
            """
            Récupère la vue mise en cache automatiquement (inspiré de mini_minecraft_pyglet_server_corrected.py).
            Cette route utilise l'image capturée périodiquement pour de meilleures performances.
            """
            with self.image_lock:
                if self.latest_image is None:
                    # Si pas d'image en cache, essayer une capture directe
                    if self.window and HAS_DISPLAY:
                        screenshot = self._take_screenshot()
                        if screenshot:
                            return StreamingResponse(
                                io.BytesIO(screenshot),
                                media_type="image/png"
                            )
                    
                    # Retourner une image vide si rien n'est disponible
                    from PIL import Image as PILImage
                    img = PILImage.new('RGB', (800, 600), (0, 0, 0))
                    bio = io.BytesIO()
                    img.save(bio, format='PNG')
                    bio.seek(0)
                    return StreamingResponse(bio, media_type="image/png")
                else:
                    # Utiliser l'image mise en cache
                    img = self.latest_image.copy()
            
            bio = io.BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)
            return StreamingResponse(bio, media_type="image/png")
        
        @self.app.get("/status")
        async def get_status():
            """Récupère le statut complet du client."""
            if not self.window:
                return {
                    "running": False,
                    "gui_enabled": self.enable_gui,
                    "auto_capture": self.auto_capture,
                    "has_cached_image": self.latest_image is not None
                }
            
            return {
                "running": self.running,
                "gui_enabled": self.enable_gui,
                "auto_capture": self.auto_capture,
                "capture_interval": self.capture_interval,
                "has_cached_image": self.latest_image is not None,
                "position": self.get_position(),
                "rotation": self.window.rotation,
                "flying": self.window.flying,
                "block_type": getattr(self.default_block_type, 'name', str(self.default_block_type)),
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
        
        # Critical safety check: only allow screenshots when pyglet app is fully running
        if not self.app_running:
            print("Screenshot error: Application not fully initialized")
            return None
        
        # Additional safety check: ensure we have the real MinecraftWindow and not the dummy
        if self.window.__class__.__name__ != 'MinecraftWindow' or not hasattr(self.window, 'context'):
            print("Screenshot error: No proper window context available")
            return None
        
        try:
            # Check if window has proper OpenGL context and required methods
            if not hasattr(self.window, 'get_size') or not hasattr(self.window, 'dispatch_event'):
                print("Screenshot error: Window missing required methods")
                return None
            
            # Extra safety: wrap all OpenGL calls in try-catch
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
                
            except Exception as gl_error:
                print(f"Screenshot error: OpenGL operation failed: {gl_error}")
                return None
            
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None
    
    def capture_frame(self, dt):
        """
        Capture l'image du buffer dans le thread principal de Pyglet (inspiré de mini_minecraft_pyglet_server_corrected.py).
        Cette méthode est appelée périodiquement pour maintenir un cache d'images.
        """
        if not self.auto_capture or not self.window:
            return
        
        try:
            # Capture de l'écran
            screenshot_bytes = self._take_screenshot()
            if screenshot_bytes:
                # Convertir les bytes en image PIL pour le cache
                screenshot_image = Image.open(io.BytesIO(screenshot_bytes))
                
                # Stocker l'image de manière thread-safe
                with self.image_lock:
                    self.latest_image = screenshot_image
                    
        except Exception as e:
            print(f"⚠️  Erreur capture frame automatique: {e}")
    
    def get_position(self) -> Optional[Tuple[float, float, float]]:
        """Récupère la position actuelle du joueur."""
        return self.window.position if self.window else None
    
    def _display_api_endpoints(self):
        """Affiche tous les endpoints API disponibles au terminal."""
        print()
        print("📋 Endpoints API disponibles:")
        print("=" * 50)
        print()
        
        # Information générale
        print(f"  GET  /                  - Informations générales de l'API")
        print(f"  GET  /status            - Statut complet du client")
        print(f"  GET  /docs              - Documentation interactive Swagger")
        print()
        
        # Mouvement
        print("  Mouvement:")
        print(f"  POST /move              - Mouvement relatif")
        print(f"       ?dx=X&dy=Y&dz=Z    (ex: ?dx=10&dy=5&dz=-5)")
        print(f"  POST /teleport          - Téléportation absolue")
        print(f"       ?x=X&y=Y&z=Z       (ex: ?x=100&y=50&z=100)")
        print()
        
        # Blocs
        print("  Blocs:")
        print(f"  POST /place_block       - Placer un bloc")
        print(f"       ?x=X&y=Y&z=Z&block_type=TYPE")
        print(f"  POST /remove_block      - Supprimer un bloc")
        print(f"       ?x=X&y=Y&z=Z")
        print()
        
        # Vue
        print("  Vue:")
        print(f"  GET  /get_view          - Capture d'écran immédiate (PNG)")
        print(f"  GET  /view              - Vue mise en cache (PNG, plus rapide)")
        print()
        
        # Exemples pratiques
        print("  Exemples d'utilisation:")
        base_url = f"http://{self.server_host}:{self.server_port}"
        print(f"  curl {base_url}/status")
        print(f"  curl -X POST '{base_url}/teleport?x=100&y=50&z=100'")
        print(f"  curl -X POST '{base_url}/place_block?x=101&y=50&z=101&block_type=STONE'")
        print(f"  curl {base_url}/get_view -o screenshot.png")
        print(f"  curl {base_url}/view -o cached_view.png  # Plus rapide")
        print()
        print("=" * 50)
    
    def start_server(self) -> bool:
        """Démarre le serveur FastAPI dans un thread séparé."""
        if self.server_thread and self.server_thread.is_alive():
            print("Server already running")
            return True
        
        def run_server():
            try:
                uvicorn.run(self.app, host=self.server_host, port=self.server_port, log_level="warning")
            except Exception as e:
                print(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait longer and test connection
        max_attempts = 10
        for attempt in range(max_attempts):
            time.sleep(1)
            try:
                import requests
                response = requests.get(f"http://{self.server_host}:{self.server_port}/", timeout=2)
                if response.status_code == 200:
                    break
            except:
                if attempt == max_attempts - 1:
                    print("⚠️ Server may not be fully ready yet")
                continue
        
        print(f"🚀 FastAPI server started on http://{self.server_host}:{self.server_port}")
        print(f"📊 API documentation: http://{self.server_host}:{self.server_port}/docs")
        
        # Display all available API endpoints
        self._display_api_endpoints()
        
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
                
                # Set app_running flag before starting pyglet app
                self.app_running = True
                
                # Schedule periodic image capture (inspired by mini_minecraft_pyglet_server_corrected.py)
                if self.auto_capture and HAS_DISPLAY:
                    pyglet.clock.schedule_interval(self.capture_frame, self.capture_interval)
                    print(f"📸 Image capture scheduled every {self.capture_interval}s")
                
                pyglet.app.run()
                
            except Exception as e:
                print(f"❌ Client error: {e}")
                raise
            finally:
                self.running = False
                self.app_running = False
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
    
    parser = argparse.ArgumentParser(description="Minecraft Client with FastAPI integration and auto-capture")
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
    parser.add_argument('--no-auto-capture', action='store_true',
                       help='Disable automatic image capture')
    parser.add_argument('--capture-interval', type=float, default=0.1,
                       help='Interval between image captures in seconds (default: 0.1)')
    
    args = parser.parse_args()
    
    # Create and configure client
    client = MinecraftClient(
        position=tuple(args.position),
        block_type=args.block_type,
        server_host=args.server_host,
        server_port=args.server_port,
        enable_gui=not args.headless,
        auto_capture=not args.no_auto_capture,
        capture_interval=args.capture_interval
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