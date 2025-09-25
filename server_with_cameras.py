#!/usr/bin/env python3
"""
Serveur Minecraft avec caméras FastAPI
Minecraft Server with FastAPI Cameras

Lance le serveur Minecraft et le serveur FastAPI de caméras simultanément.
"""

import asyncio
import logging
import signal
from server import MinecraftServer
from fastapi_camera_server import fastapi_camera_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MinecraftServerWithCameras:
    """Serveur combiné Minecraft + FastAPI cameras."""
    
    def __init__(self):
        self.minecraft_server = MinecraftServer()
        self.fastapi_server = fastapi_camera_server
        self.running = False
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Démarre les deux serveurs."""
        self.running = True
        
        try:
            # Démarrer les tâches en parallèle
            minecraft_task = asyncio.create_task(self.minecraft_server.start_server())
            fastapi_task = asyncio.create_task(self.fastapi_server.start_server())
            
            self.logger.info("🚀 Serveurs démarrés!")
            self.logger.info("🎮 Serveur Minecraft: ws://localhost:8765")
            self.logger.info("📹 Interface caméras: http://localhost:8080")
            
            # Attendre les deux serveurs
            await asyncio.gather(minecraft_task, fastapi_task)
            
        except Exception as e:
            self.logger.error(f"Erreur serveur: {e}")
            raise
        finally:
            self.running = False
    
    def stop(self):
        """Arrête les serveurs."""
        self.minecraft_server.stop_server()
        self.running = False


async def main():
    """Point d'entrée principal."""
    combined_server = MinecraftServerWithCameras()
    
    # Gérer les signaux d'arrêt
    def signal_handler(signum, frame):
        print(f"\nSignal {signum} reçu, arrêt des serveurs...")
        combined_server.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await combined_server.start()
    except KeyboardInterrupt:
        combined_server.stop()
        print("Serveurs arrêtés par l'utilisateur")
    except Exception as e:
        logging.error(f"Erreur critique: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())