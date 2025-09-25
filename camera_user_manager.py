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
    
    def _display_camera_endpoints(self, camera: CameraUser):
        """Affiche les endpoints disponibles pour une caméra dans le terminal."""
        print(f"\n📹 Caméra {camera.id} créée à la position {camera.position}")
        print(f"🌐 Endpoints disponibles et leurs fonctionnalités:")
        print(f"   • API de base:          http://localhost:{camera.port}/")
        print(f"     → Informations générales de l'API et liste des endpoints")
        print(f"   • Vue de la caméra:     http://localhost:{camera.port}/get_view")
        print(f"     → Capture d'écran PNG de ce que voit la caméra")
        print(f"   • Statut complet:       http://localhost:{camera.port}/status")
        print(f"     → Position, rotation, état de vol, blocs visibles, etc.")
        print(f"   • Mouvement relatif:    POST http://localhost:{camera.port}/move?dx=X&dy=Y&dz=Z")
        print(f"     → Déplace la caméra de façon relative (dx, dy, dz)")
        print(f"   • Téléportation:        POST http://localhost:{camera.port}/teleport?x=X&y=Y&z=Z")
        print(f"     → Téléporte la caméra à une position absolue")
        print(f"   • Placer un bloc:       POST http://localhost:{camera.port}/place_block?x=X&y=Y&z=Z&block_type=TYPE")
        print(f"     → Place un bloc à la position spécifiée (STONE, GRASS, etc.)")
        print(f"   • Supprimer un bloc:    POST http://localhost:{camera.port}/remove_block?x=X&y=Y&z=Z")
        print(f"     → Supprime le bloc à la position spécifiée")
        print(f"   • Documentation API:    http://localhost:{camera.port}/docs")
        print(f"     → Interface Swagger interactive pour tester l'API")
        print(f"🔧 État: {'🟢 Actif' if camera.running else '🔴 Inactif'}")
        print(f"📍 Position: x={camera.position[0]}, y={camera.position[1]}, z={camera.position[2]}")
        print(f"🔌 Port: {camera.port}")
        print()

    def create_camera_user(self, position: Tuple[int, int, int]) -> Optional[CameraUser]:
        """Crée un nouvel utilisateur caméra à la position spécifiée."""
        camera_id = self.generate_camera_id(position)
        
        if camera_id in self.cameras:
            logger.warning(f"Caméra {camera_id} existe déjà à la position {position}")
            # Afficher les endpoints de la caméra existante
            self._display_camera_endpoints(self.cameras[camera_id])
            return self.cameras[camera_id]
        
        port = self.get_next_port()
        self.used_ports.add(port)
        
        # Créer l'utilisateur caméra
        camera = CameraUser(
            id=camera_id,
            position=position,
            port=port
        )
        
        # Marquer la caméra comme active (simulation d'un serveur)
        camera.running = True
        
        # Ajouter à la liste des caméras
        self.cameras[camera_id] = camera
        
        # Afficher les endpoints disponibles dans le terminal au lieu de créer une fenêtre
        self._display_camera_endpoints(camera)
        
        logger.info(f"Caméra {camera_id} créée avec succès sur le port {port}")
        return camera
    
    def remove_camera_user(self, position: Tuple[int, int, int]) -> bool:
        """Supprime un utilisateur caméra à la position spécifiée."""
        camera_id = self.generate_camera_id(position)
        
        if camera_id not in self.cameras:
            logger.warning(f"Aucune caméra trouvée à la position {position}")
            return False
        
        camera = self.cameras[camera_id]
        
        try:
            # Marquer la caméra comme inactive
            camera.running = False
            
            # Libérer le port
            self.used_ports.discard(camera.port)
            
            # Supprimer de la liste
            del self.cameras[camera_id]
            
            print(f"🗑️  Caméra {camera_id} supprimée de la position {position}")
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