#!/usr/bin/env python3
"""
Minecraft Client Abstracted - Classe Client Abstraite
====================================================

Cette classe abstrait le code de minecraft_client_fr.py pour permettre:
- Un client utilisable par un humain pour jouer
- Support pour position, type de bloc configurables

Usage:
    from minecraft_client import MinecraftClient
    
    client = MinecraftClient(position=[30, 50, 80], block_type="GRASS")
    client.run()  # Démarre le client graphique
"""

import sys
import math
import time
from typing import Optional, Tuple

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
    Classe client Minecraft abstraite.
    
    Cette classe permet de contrôler un client Minecraft via l'interface graphique.
    """
    
    def __init__(self, 
                 position: Optional[Tuple[float, float, float]] = None,
                 block_type: str = "GRASS",
                 enable_gui: bool = True):
        """
        Initialise le client Minecraft.
        
        Args:
            position: Position initiale (x, y, z) du joueur
            block_type: Type de bloc par défaut 
            enable_gui: Active/désactive l'interface graphique
        """
        self.enable_gui = enable_gui
        
        # Position initiale
        if position:
            config.set("player", "preferred_spawn", list(position))
        
        # Configuration du bloc par défaut
        self.default_block_type = getattr(BlockType, block_type.upper(), BlockType.GRASS)
        
        # État du client
        self.window = None
        self.running = False
        self.app_running = False  # Track if pyglet app is running

    
    def get_position(self) -> Optional[Tuple[float, float, float]]:
        """Récupère la position actuelle du joueur."""
        return self.window.position if self.window else None
    
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
                
                # Set app_running flag before starting pyglet app
                self.app_running = True
                
                pyglet.app.run()
                
            except Exception as e:
                print(f"❌ Client error: {e}")
                raise
            finally:
                self.running = False
                self.app_running = False
        else:
            # Headless mode - create a minimal window object
            print("🔧 Running in headless mode")
            self.window = MinecraftWindow()  # Create dummy window
            self.running = True
            
            print("✅ Headless client started successfully!")
            print(f"🎯 Starting position: {self.window.position}")
            print(f"🧱 Default block: {getattr(self.default_block_type, 'name', self.default_block_type)}")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Client stopped by user")
            finally:
                self.running = False


def main():
    """Point d'entrée principal pour tester la classe client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Minecraft Client")
    parser.add_argument('--position', nargs=3, type=float, default=[30, 50, 80],
                       help='Starting position [x y z]')
    parser.add_argument('--block-type', default='GRASS', 
                       help='Default block type')
    parser.add_argument('--headless', action='store_true',
                       help='Run without GUI')
    
    args = parser.parse_args()
    
    # Create and configure client
    client = MinecraftClient(
        position=tuple(args.position),
        block_type=args.block_type,
        enable_gui=not args.headless
    )
    
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