"""
Gestionnaire d'utilisateurs avec serveurs RTSP
User Manager with RTSP servers for vision streaming
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class RTSPUser:
    """Représente un utilisateur avec un serveur RTSP pour sa vision."""
    id: str
    name: str
    rtsp_port: int
    rtsp_url: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float]
    is_active: bool = True
    
    def to_dict(self) -> dict:
        """Convertit l'utilisateur en dictionnaire."""
        return asdict(self)


class UserManager:
    """Gestionnaire des utilisateurs avec serveurs RTSP intégrés."""
    
    def __init__(self, config_file: str = "users_config.json"):
        """
        Initialise le gestionnaire d'utilisateurs.
        
        Args:
            config_file: Chemin vers le fichier de configuration des utilisateurs
        """
        self.config_file = config_file
        self.users: Dict[str, RTSPUser] = {}
        self.rtsp_servers: Dict[str, 'RTSPServer'] = {}
        self.base_rtsp_port = 8554
        self.logger = logging.getLogger(__name__)
        
        # Configuration par défaut des utilisateurs
        self.default_users_config = {
            "users": [
                {
                    "name": "Observateur_1",
                    "rtsp_port": 8554,
                    "position": [30, 50, 80],
                    "rotation": [0, 0]
                },
                {
                    "name": "Observateur_2", 
                    "rtsp_port": 8555,
                    "position": [50, 50, 60],
                    "rotation": [90, 0]
                },
                {
                    "name": "Observateur_3",
                    "rtsp_port": 8556,
                    "position": [70, 50, 40],
                    "rotation": [180, 0]
                }
            ],
            "rtsp_settings": {
                "host": "localhost",
                "resolution": "1280x720",
                "fps": 30,
                "bitrate": 2000000
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
    
    def create_startup_users(self) -> List[RTSPUser]:
        """Crée les utilisateurs au démarrage selon la configuration."""
        created_users = []
        
        for user_config in self.users_config.get("users", []):
            user = self._create_user_from_config(user_config)
            if user:
                self.users[user.id] = user
                created_users.append(user)
                self.logger.info(f"Utilisateur créé: {user.name} (RTSP: {user.rtsp_url})")
        
        self.logger.info(f"Total {len(created_users)} utilisateurs créés au démarrage")
        return created_users
    
    def _create_user_from_config(self, user_config: dict) -> Optional[RTSPUser]:
        """Crée un utilisateur à partir de la configuration."""
        try:
            user_id = str(uuid.uuid4())
            rtsp_host = self.users_config.get("rtsp_settings", {}).get("host", "localhost")
            rtsp_port = user_config.get("rtsp_port", self.base_rtsp_port)
            
            user = RTSPUser(
                id=user_id,
                name=user_config["name"],
                rtsp_port=rtsp_port,
                rtsp_url=f"rtsp://{rtsp_host}:{rtsp_port}/stream",
                position=tuple(user_config.get("position", [0, 50, 0])),
                rotation=tuple(user_config.get("rotation", [0, 0]))
            )
            
            return user
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            return None
    
    def get_user(self, user_id: str) -> Optional[RTSPUser]:
        """Récupère un utilisateur par son ID."""
        return self.users.get(user_id)
    
    def get_all_users(self) -> List[RTSPUser]:
        """Récupère tous les utilisateurs."""
        return list(self.users.values())
    
    def get_active_users(self) -> List[RTSPUser]:
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
    
    async def start_rtsp_servers(self) -> None:
        """Démarre les serveurs RTSP pour tous les utilisateurs actifs."""
        for user in self.get_active_users():
            try:
                rtsp_server = RTSPServer(user)
                await rtsp_server.start()
                self.rtsp_servers[user.id] = rtsp_server
                self.logger.info(f"Serveur RTSP démarré pour {user.name} sur {user.rtsp_url}")
            except Exception as e:
                self.logger.error(f"Erreur lors du démarrage du serveur RTSP pour {user.name}: {e}")
    
    async def stop_rtsp_servers(self) -> None:
        """Arrête tous les serveurs RTSP."""
        for user_id, server in self.rtsp_servers.items():
            try:
                await server.stop()
                self.logger.info(f"Serveur RTSP arrêté pour utilisateur {user_id}")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'arrêt du serveur RTSP: {e}")
        
        self.rtsp_servers.clear()
    
    def get_rtsp_urls(self) -> Dict[str, str]:
        """Retourne les URLs RTSP de tous les utilisateurs actifs."""
        return {user.name: user.rtsp_url for user in self.get_active_users()}


class RTSPServer:
    """Serveur RTSP simplifié pour streaming de la vision d'un utilisateur."""
    
    def __init__(self, user: RTSPUser):
        """
        Initialise le serveur RTSP pour un utilisateur.
        
        Args:
            user: L'utilisateur associé à ce serveur RTSP
        """
        self.user = user
        self.is_running = False
        self.logger = logging.getLogger(f"{__name__}.{user.name}")
        
    async def start(self) -> None:
        """Démarre le serveur RTSP."""
        if self.is_running:
            return
            
        try:
            # Simulation du démarrage d'un serveur RTSP
            # Dans une implémentation réelle, ceci démarrerait un vrai serveur RTSP
            self.is_running = True
            self.logger.info(f"Serveur RTSP simulé démarré sur {self.user.rtsp_url}")
            
            # Démarrage du stream de vision en arrière-plan
            asyncio.create_task(self._stream_vision())
            
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du serveur RTSP: {e}")
            raise
    
    async def stop(self) -> None:
        """Arrête le serveur RTSP."""
        if not self.is_running:
            return
            
        self.is_running = False
        self.logger.info(f"Serveur RTSP arrêté pour {self.user.name}")
    
    async def _stream_vision(self) -> None:
        """Simule le streaming de la vision de l'utilisateur."""
        while self.is_running:
            try:
                # Simulation de la capture et diffusion de la vision
                # Dans une implémentation réelle, ceci capturerait le rendu du joueur
                # et le diffuserait via RTSP
                
                # Pour l'instant, nous simulons avec un simple log périodique
                await asyncio.sleep(1.0)  # 1 FPS pour la simulation
                
            except Exception as e:
                self.logger.error(f"Erreur dans le stream de vision: {e}")
                break


# Instance globale du gestionnaire d'utilisateurs
user_manager = UserManager()