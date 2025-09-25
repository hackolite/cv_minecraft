#!/usr/bin/env python3
"""
Camera User Manager - Gestionnaire d'utilisateurs caméra
========================================================

Ce module gère la création automatique d'utilisateurs avec serveurs FastAPI
quand des blocs caméra sont placés dans le monde Minecraft.

Fonctionnalités:
- Création d'utilisateurs caméra avec serveurs FastAPI individuels
- Gestion des ports uniques pour chaque caméra
- Surveillance des blocs caméra placés/supprimés
- API pour récupérer la liste des caméras actives
"""

import threading
import time
import asyncio
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

from minecraft_client import MinecraftClient
from protocol import BlockType

# Configuration
CAMERA_PORT_START = 8081  # Port de départ pour les caméras (8080 est souvent utilisé par le client principal)
CAMERA_USER_PREFIX = "Camera"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CameraUser:
    """Représente un utilisateur caméra avec son serveur FastAPI."""
    id: str
    position: Tuple[int, int, int]
    port: int
    client: Optional[MinecraftClient] = None
    thread: Optional[threading.Thread] = None
    running: bool = False

class CameraUserManager:
    """Gestionnaire global des utilisateurs caméra."""
    
    def __init__(self):
        self.cameras: Dict[str, CameraUser] = {}
        self.used_ports: set = set()
        self.next_camera_id = 1
        
    def get_next_port(self) -> int:
        """Trouve le prochain port disponible pour une caméra."""
        port = CAMERA_PORT_START
        while port in self.used_ports:
            port += 1
        return port
    
    def generate_camera_id(self, position: Tuple[int, int, int]) -> str:
        """Génère un ID unique pour une caméra basé sur sa position."""
        return f"{CAMERA_USER_PREFIX}_{position[0]}_{position[1]}_{position[2]}"
    
    def create_camera_user(self, position: Tuple[int, int, int]) -> Optional[CameraUser]:
        """Crée un nouvel utilisateur caméra à la position spécifiée."""
        camera_id = self.generate_camera_id(position)
        
        if camera_id in self.cameras:
            logger.warning(f"Caméra {camera_id} existe déjà à la position {position}")
            return self.cameras[camera_id]
        
        port = self.get_next_port()
        self.used_ports.add(port)
        
        # Créer l'utilisateur caméra
        camera = CameraUser(
            id=camera_id,
            position=position,
            port=port
        )
        
        # Créer le client Minecraft pour cette caméra
        try:
            camera.client = MinecraftClient(
                position=(float(position[0]), float(position[1]) + 1.0, float(position[2])),  # Un bloc au-dessus
                block_type="STONE",  # Type de bloc par défaut pour la caméra
                server_host="localhost",
                server_port=port,
                enable_gui=False  # Mode headless pour les caméras
            )
            
            # Démarrer le serveur FastAPI dans un thread séparé
            def run_camera():
                try:
                    camera.running = True
                    logger.info(f"Démarrage de la caméra {camera_id} sur le port {port}")
                    camera.client.start_server()
                    camera.client.run()
                except Exception as e:
                    logger.error(f"Erreur lors du démarrage de la caméra {camera_id}: {e}")
                    camera.running = False
            
            camera.thread = threading.Thread(target=run_camera, daemon=True)
            camera.thread.start()
            
            # Attendre un peu pour que le serveur démarre
            time.sleep(1)
            
            self.cameras[camera_id] = camera
            logger.info(f"Caméra {camera_id} créée avec succès sur le port {port}")
            return camera
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la caméra {camera_id}: {e}")
            self.used_ports.discard(port)
            return None
    
    def remove_camera_user(self, position: Tuple[int, int, int]) -> bool:
        """Supprime un utilisateur caméra à la position spécifiée."""
        camera_id = self.generate_camera_id(position)
        
        if camera_id not in self.cameras:
            logger.warning(f"Aucune caméra trouvée à la position {position}")
            return False
        
        camera = self.cameras[camera_id]
        
        try:
            # Arrêter le client si il existe
            if camera.client:
                camera.running = False
                # Note: Nous ne pouvons pas facilement arrêter le serveur FastAPI
                # Il se fermera quand le thread principal se terminera
                
            # Libérer le port
            self.used_ports.discard(camera.port)
            
            # Supprimer de la liste
            del self.cameras[camera_id]
            
            logger.info(f"Caméra {camera_id} supprimée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la caméra {camera_id}: {e}")
            return False
    
    def get_cameras(self) -> List[Dict]:
        """Retourne la liste de toutes les caméras actives."""
        cameras_info = []
        for camera in self.cameras.values():
            cameras_info.append({
                "id": camera.id,
                "position": camera.position,
                "port": camera.port,
                "running": camera.running,
                "url": f"http://localhost:{camera.port}",
                "view_endpoint": f"http://localhost:{camera.port}/get_view"
            })
        return cameras_info
    
    def get_camera_at_position(self, position: Tuple[int, int, int]) -> Optional[CameraUser]:
        """Récupère la caméra à une position donnée."""
        camera_id = self.generate_camera_id(position)
        return self.cameras.get(camera_id)

# Instance globale du gestionnaire
camera_manager = CameraUserManager()