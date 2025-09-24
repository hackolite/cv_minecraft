"""
Gestionnaire d'utilisateurs avec serveurs RTSP
User Manager with RTSP servers for vision streaming
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
from rtsp_video_streamer import EnhancedRTSPServer

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
                # Créer une caméra d'observateur pour cet utilisateur
                camera = camera_manager.create_camera(
                    observer_id=user.id,
                    position=user.position,
                    rotation=user.rotation,
                    resolution=(640, 480)
                )
                
                # Démarrer la capture de la caméra
                camera.start_capture(None)  # Pas de modèle du monde pour l'instant
                
                # Créer le serveur RTSP amélioré avec streaming vidéo
                rtsp_server = EnhancedRTSPServer(user, camera)
                await rtsp_server.start()
                self.rtsp_servers[user.id] = rtsp_server
                self.logger.info(f"Serveur RTSP avec streaming vidéo démarré pour {user.name} sur {user.rtsp_url}")
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
        
        # Arrêter toutes les caméras
        camera_manager.stop_all_cameras()
        self.rtsp_servers.clear()
    
    def get_rtsp_urls(self) -> Dict[str, str]:
        """Retourne les URLs RTSP de tous les utilisateurs actifs."""
        return {user.name: user.rtsp_url for user in self.get_active_users()}
    
    def set_world_model(self, world_model):
        """Définit le modèle du monde pour les caméras."""
        camera_manager.set_world_model(world_model)
        
    def update_observer_position(self, user_id: str, position: Tuple[float, float, float], 
                               rotation: Tuple[float, float] = None) -> bool:
        """Met à jour la position d'un observateur et de sa caméra."""
        success = self.update_user_position(user_id, position, rotation)
        if success:
            camera_manager.update_camera_position(user_id, position, rotation)
        return success


class RTSPServer:
    """Serveur RTSP pour streaming de la vision d'un utilisateur."""
    
    def __init__(self, user: RTSPUser):
        """
        Initialise le serveur RTSP pour un utilisateur.
        
        Args:
            user: L'utilisateur associé à ce serveur RTSP
        """
        self.user = user
        self.is_running = False
        self.logger = logging.getLogger(f"{__name__}.{user.name}")
        self.server_socket = None
        self.server_task = None
        
    async def start(self) -> None:
        """Démarre le serveur RTSP."""
        if self.is_running:
            return
            
        try:
            # Créer le socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.user.rtsp_port))
            self.server_socket.listen(5)
            
            self.is_running = True
            self.logger.info(f"Serveur RTSP démarré sur {self.user.rtsp_url}")
            
            # Démarrer l'acceptation des connexions en arrière-plan avec executor
            self.server_task = asyncio.create_task(self._run_server())
            
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du serveur RTSP: {e}")
            raise
    
    async def stop(self) -> None:
        """Arrête le serveur RTSP."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Annuler la tâche serveur
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
        
        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        self.logger.info(f"Serveur RTSP arrêté pour {self.user.name}")
    
    async def _run_server(self):
        """Exécute le serveur RTSP dans un thread."""
        import threading
        import concurrent.futures
        
        def server_thread():
            """Thread qui fait tourner le serveur RTSP synchrone."""
            while self.is_running:
                try:
                    self.server_socket.settimeout(1.0)  # Timeout pour vérifier is_running
                    try:
                        client_socket, addr = self.server_socket.accept()
                        self.logger.info(f"Connexion RTSP de {addr}")
                        
                        # Créer un thread pour gérer ce client
                        client_thread = threading.Thread(
                            target=self._handle_client_sync,
                            args=(client_socket, addr),
                            daemon=True
                        )
                        client_thread.start()
                        
                    except socket.timeout:
                        continue  # Timeout normal, continuer la boucle
                        
                except Exception as e:
                    if self.is_running:
                        self.logger.error(f"Erreur serveur RTSP: {e}")
                    break
        
        # Exécuter le serveur dans un thread
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            try:
                await loop.run_in_executor(executor, server_thread)
            except asyncio.CancelledError:
                pass
    
    def _handle_client_sync(self, client_socket, addr):
        """Gère un client RTSP connecté (version synchrone)."""
        try:
            client_socket.settimeout(30.0)  # Timeout pour les opérations client
            
            while self.is_running:
                try:
                    # Recevoir la requête du client
                    data = client_socket.recv(4096)
                    if not data:
                        break
                        
                    request = data.decode('utf-8', errors='ignore')
                    self.logger.info(f"Requête RTSP de {addr}: {request.split()[0]} {request.split()[1] if len(request.split()) > 1 else ''}")
                    
                    # Parser la requête RTSP
                    lines = request.strip().split('\r\n')
                    if not lines:
                        continue
                        
                    request_line = lines[0]
                    headers = {}
                    
                    for line in lines[1:]:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            headers[key.strip().lower()] = value.strip()
                    
                    # Extraire le CSeq pour la réponse
                    cseq = headers.get('cseq', '1')
                    
                    # Gérer différents types de requêtes RTSP
                    if request_line.startswith('OPTIONS'):
                        response = self._create_options_response(cseq)
                    elif request_line.startswith('DESCRIBE'):
                        response = self._create_describe_response(cseq)
                    elif request_line.startswith('SETUP'):
                        response = self._create_setup_response(cseq, headers)
                    elif request_line.startswith('PLAY'):
                        response = self._create_play_response(cseq)
                    elif request_line.startswith('TEARDOWN'):
                        response = self._create_teardown_response(cseq)
                        client_socket.send(response.encode())
                        break
                    else:
                        response = self._create_error_response(cseq, '501 Not Implemented')
                    
                    # Envoyer la réponse
                    client_socket.send(response.encode())
                    self.logger.debug(f"Réponse envoyée à {addr}")
                    
                except socket.timeout:
                    # Timeout client
                    break
                except Exception as e:
                    self.logger.error(f"Erreur lors du traitement de la requête de {addr}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Erreur dans la gestion du client {addr}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            self.logger.info(f"Client RTSP {addr} déconnecté")
    
    def _create_options_response(self, cseq):
        """Crée une réponse OPTIONS."""
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Public: OPTIONS, DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE\r\n"
            f"\r\n"
        )
    
    def _create_describe_response(self, cseq):
        """Crée une réponse DESCRIBE avec SDP."""
        sdp_content = (
            f"v=0\r\n"
            f"o=- 123456 654321 IN IP4 localhost\r\n"
            f"s={self.user.name} Stream\r\n"
            f"t=0 0\r\n"
            f"m=video 0 RTP/AVP 96\r\n"
            f"a=rtpmap:96 H264/90000\r\n"
            f"a=control:track1\r\n"
        )
        
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Content-Type: application/sdp\r\n"
            f"Content-Length: {len(sdp_content)}\r\n"
            f"\r\n"
            f"{sdp_content}"
        )
    
    def _create_setup_response(self, cseq, headers):
        """Crée une réponse SETUP."""
        # Générer un ID de session simple
        session_id = f"session_{self.user.rtsp_port}"
        
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Session: {session_id}\r\n"
            f"Transport: RTP/AVP;unicast;client_port=8000-8001;server_port=8002-8003\r\n"
            f"\r\n"
        )
    
    def _create_play_response(self, cseq):
        """Crée une réponse PLAY."""
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Range: npt=0.000-\r\n"
            f"RTP-Info: url=rtsp://localhost:{self.user.rtsp_port}/stream/track1\r\n"
            f"\r\n"
        )
    
    def _create_teardown_response(self, cseq):
        """Crée une réponse TEARDOWN."""
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"\r\n"
        )
    
    def _create_error_response(self, cseq, error):
        """Crée une réponse d'erreur."""
        return (
            f"RTSP/1.0 {error}\r\n"
            f"CSeq: {cseq}\r\n"
            f"\r\n"
        )


# Instance globale du gestionnaire d'utilisateurs
user_manager = UserManager()