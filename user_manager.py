"""
Gestionnaire d'utilisateurs avec serveur FastAPI
User Manager with FastAPI server for vision streaming
"""

import asyncio
import json
import logging
import socket
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Import des nouveaux modules pour le streaming vidéo
from observer_camera import camera_manager, ObserverCamera

@dataclass
class CameraUser:
    """Représente un utilisateur avec une caméra d'observateur."""
    id: str
    name: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float]
    is_active: bool = True
    
    def to_dict(self) -> dict:
        """Convertit l'utilisateur en dictionnaire."""
        return asdict(self)


class UserManager:
    """Gestionnaire des utilisateurs avec serveur FastAPI intégré."""
    
    def __init__(self, config_file: str = "users_config.json"):
        """
        Initialise le gestionnaire d'utilisateurs.
        
        Args:
            config_file: Chemin vers le fichier de configuration des utilisateurs
        """
        self.config_file = config_file
        self.users: Dict[str, CameraUser] = {}
        self.fastapi_server = None
        self.logger = logging.getLogger(__name__)
        
        # Configuration par défaut des utilisateurs
        self.default_users_config = {
            "users": [
                {
                    "name": "Observateur_1",
                    "position": [30, 50, 80],
                    "rotation": [0, 0]
                },
                {
                    "name": "Observateur_2", 
                    "position": [50, 50, 60],
                    "rotation": [90, 0]
                },
                {
                    "name": "Observateur_3",
                    "position": [70, 50, 40],
                    "rotation": [180, 0]
                }
            ],
            "camera_settings": {
                "host": "localhost",
                "port": 8080,
                "resolution": "640x480",
                "fps": 30
            }
        }
        
        self.load_users_config()
        
    def load_users_config(self) -> None:
        """Charge la configuration des utilisateurs."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            self.logger.info(f"Configuration utilisateurs non trouvée, création de {self.config_file}")
            config = self.default_users_config
            self.save_users_config(config)
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            config = self.default_users_config
            
        self.users_config = config
        
    def save_users_config(self, config: dict = None) -> None:
        """Sauvegarde la configuration des utilisateurs."""
        if config is None:
            config = self.users_config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Configuration utilisateurs sauvegardée dans {self.config_file}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def create_startup_users(self) -> List[CameraUser]:
        """Crée les utilisateurs au démarrage selon la configuration."""
        created_users = []
        
        for user_config in self.users_config.get("users", []):
            user = self._create_user_from_config(user_config)
            if user:
                self.users[user.id] = user
                created_users.append(user)
                self.logger.info(f"Utilisateur créé: {user.name}")
        
        self.logger.info(f"Total {len(created_users)} utilisateurs créés au démarrage")
        return created_users
    
    def _create_user_from_config(self, user_config: dict) -> Optional[CameraUser]:
        """Crée un utilisateur à partir de la configuration."""
        try:
            user_id = str(uuid.uuid4())
            
            user = CameraUser(
                id=user_id,
                name=user_config["name"],
                position=tuple(user_config.get("position", [0, 50, 0])),
                rotation=tuple(user_config.get("rotation", [0, 0]))
            )
            
            return user
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            return None
    
    def get_user(self, user_id: str) -> Optional[CameraUser]:
        """Récupère un utilisateur par son ID."""
        return self.users.get(user_id)
    
    def get_all_users(self) -> List[CameraUser]:
        """Récupère tous les utilisateurs."""
        return list(self.users.values())
    
    def get_active_users(self) -> List[CameraUser]:
        """Récupère tous les utilisateurs actifs."""
        return [user for user in self.users.values() if user.is_active]
    
    def update_user_position(self, user_id: str, position: Tuple[float, float, float], 
                           rotation: Tuple[float, float] = None) -> bool:
        """Met à jour la position d'un utilisateur."""
        user = self.users.get(user_id)
        if user:
            user.position = position
            if rotation:
                user.rotation = rotation
            return True
        return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """Désactive un utilisateur."""
        user = self.users.get(user_id)
        if user:
            user.is_active = False
            return True
        return False
    
    def activate_user(self, user_id: str) -> bool:
        """Active un utilisateur."""
        user = self.users.get(user_id)
        if user:
            user.is_active = True
            return True
        return False
    
    async def start_camera_server(self) -> None:
        """Démarre le serveur FastAPI pour toutes les caméras."""
        from fastapi_camera_server import fastapi_camera_server
        
        self.logger.info("Initialisation des caméras d'observateurs...")
        
        for user in self.get_active_users():
            try:
                # Créer une caméra d'observateur pour cet utilisateur
                camera = camera_manager.create_camera(
                    observer_id=user.id,
                    position=user.position,
                    rotation=user.rotation,
                    resolution=(640, 480)
                )
                
                self.logger.info(f"Caméra créée pour {user.name} à la position {user.position}")
            except Exception as e:
                self.logger.error(f"Erreur lors de la création de la caméra pour {user.name}: {e}")
        
        # Démarrer toutes les caméras avec le modèle du monde (s'il existe)
        if hasattr(camera_manager, 'world_model') and camera_manager.world_model:
            camera_manager.start_all_cameras()
            self.logger.info("Caméras démarrées avec le modèle du monde")
        else:
            # Démarrer les caméras même sans modèle du monde pour les tests
            for camera in camera_manager.get_all_cameras():
                camera.start_capture(None)
            self.logger.info("Caméras démarrées en mode test (sans modèle du monde)")
        
        # Le serveur FastAPI sera démarré séparément
        self.fastapi_server = fastapi_camera_server
    
    async def start_camera_server_with_retry(self, max_retries: int = 3) -> bool:
        """Démarre le serveur de caméras avec retry logic."""
        for attempt in range(max_retries):
            try:
                await self.start_camera_server()
                
                # Vérifier que les caméras sont actives
                active_cameras = sum(1 for camera in camera_manager.get_all_cameras() if camera.is_capturing)
                total_cameras = len(camera_manager.get_all_cameras())
                
                if active_cameras > 0:
                    self.logger.info(f"Serveur de caméras démarré avec succès ({active_cameras}/{total_cameras} caméras actives)")
                    return True
                else:
                    self.logger.warning(f"Tentative {attempt + 1}: Aucune caméra active")
                    
            except Exception as e:
                self.logger.error(f"Tentative {attempt + 1} échouée: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponentiel
        
        self.logger.error("Impossible de démarrer le serveur de caméras après plusieurs tentatives")
        return False
    
    def is_camera_server_healthy(self) -> bool:
        """Vérifie l'état de santé du serveur de caméras."""
        try:
            if not self.fastapi_server:
                return False
                
            # Vérifier les caméras actives
            cameras = camera_manager.get_all_cameras()
            if not cameras:
                return False
                
            active_cameras = sum(1 for camera in cameras if camera.is_capturing)
            return active_cameras > 0
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de santé: {e}")
            return False
    
    async def stop_camera_server(self) -> None:
        """Arrête le serveur de caméras."""
        # Arrêter toutes les caméras
        camera_manager.stop_all_cameras()
        self.logger.info("Serveur de caméras arrêté")
    
    def get_camera_urls(self) -> Dict[str, str]:
        """Retourne les URLs des caméras de tous les utilisateurs actifs."""
        settings = self.users_config.get("camera_settings", {})
        host = settings.get("host", "localhost")
        port = settings.get("port", 8080)
        
        urls = {}
        for user in self.get_active_users():
            urls[user.name] = f"http://{host}:{port}/camera/{user.id}/stream"
        return urls
    
    def get_web_interface_url(self) -> str:
        """Retourne l'URL de l'interface web."""
        settings = self.users_config.get("camera_settings", {})
        host = settings.get("host", "localhost")
        port = settings.get("port", 8080)
        return f"http://{host}:{port}/"
    
    def set_world_model(self, world_model):
        """Définit le modèle du monde pour les caméras."""
        camera_manager.set_world_model(world_model)
        
    def update_observer_position(self, user_id: str, position: Tuple[float, float, float], 
                               rotation: Tuple[float, float] = None) -> bool:
        """Met à jour la position d'un observateur et de sa caméra."""
        success = self.update_user_position(user_id, position, rotation)
        if success:
            # Mettre à jour la position de la caméra
            camera = camera_manager.get_camera(user_id)
            if camera:
                camera.update_position(position, rotation)
        return success

# Instance globale du gestionnaire d'utilisateurs
user_manager = UserManager()