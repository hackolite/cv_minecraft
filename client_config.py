"""
Configuration du client Minecraft - Client configuration
Système de configuration pour le client Minecraft avec support français.
"""

import json
import os
from typing import Dict, Any, Tuple

class ClientConfig:
    """Gestionnaire de configuration pour le client Minecraft."""
    
    DEFAULT_CONFIG = {
        # Configuration réseau / Network configuration
        "server": {
            "host": "localhost",
            "port": 8765,
            "auto_reconnect": True,
            "connection_timeout": 10
        },
        
        # Configuration graphique / Graphics configuration
        "graphics": {
            "window_width": 1280,
            "window_height": 720,
            "fullscreen": False,
            "vsync": True,
            "fov": 70.0,
            "render_distance": 60.0,
            "show_fps": True
        },
        
        # Configuration des contrôles / Controls configuration
        "controls": {
            "keyboard_layout": "azerty",  # azerty ou qwerty
            "mouse_sensitivity": 0.15,
            "invert_mouse_y": False,
            "sprint_key": "R",
            "crouch_key": "LSHIFT",
            "jump_key": "SPACE",
            "fly_toggle": "TAB",
            "chat_key": "T",
            "inventory_key": "E"
        },
        
        # Configuration de l'interface / UI configuration
        "interface": {
            "language": "fr",  # fr ou en
            "show_debug_info": True,
            "show_coordinates": True,
            "show_block_info": True,
            "crosshair_color": [255, 255, 255],
            "ui_scale": 1.0
        },
        
        # Configuration audio / Audio configuration
        "audio": {
            "master_volume": 0.5,
            "music_volume": 0.3,
            "effects_volume": 0.7,
            "muted": False
        },
        
        # Configuration du joueur / Player configuration
        "player": {
            "name": "Joueur",
            "preferred_spawn": [30, 50, 80],
            "movement_speed": 5.0,
            "jump_speed": 8.0,
            "flying_speed": 15.0
        }
    }
    
    def __init__(self, config_file: str = "client_config.json"):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Charge la configuration depuis le fichier."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self._merge_config(self.config, saved_config)
                print(f"Configuration chargée depuis {self.config_file}")
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {e}")
                print("Utilisation de la configuration par défaut")
        else:
            print("Fichier de configuration non trouvé, création avec valeurs par défaut")
            self.save_config()
    
    def save_config(self) -> None:
        """Sauvegarde la configuration dans le fichier."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"Configuration sauvegardée dans {self.config_file}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def _merge_config(self, base: Dict[str, Any], new: Dict[str, Any]) -> None:
        """Fusionne récursivement la nouvelle configuration avec la base."""
        for key, value in new.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, section: str, key: str = None, default=None):
        """
        Récupère une valeur de configuration.
        
        Args:
            section: Section de configuration (ex: 'graphics')
            key: Clé dans la section (optionnel)
            default: Valeur par défaut si non trouvée
        
        Returns:
            La valeur de configuration ou la valeur par défaut
        """
        try:
            if key is None:
                return self.config.get(section, default)
            else:
                return self.config.get(section, {}).get(key, default)
        except:
            return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Définit une valeur de configuration.
        
        Args:
            section: Section de configuration
            key: Clé dans la section
            value: Nouvelle valeur
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_server_url(self) -> str:
        """Retourne l'URL du serveur WebSocket."""
        host = self.get("server", "host", "localhost")
        port = self.get("server", "port", 8765)
        return f"ws://{host}:{port}"
    
    def get_window_size(self) -> Tuple[int, int]:
        """Retourne la taille de la fenêtre."""
        width = self.get("graphics", "window_width", 1280)
        height = self.get("graphics", "window_height", 720)
        return width, height
    
    def is_azerty_layout(self) -> bool:
        """Vérifie si le layout clavier est AZERTY."""
        return self.get("controls", "keyboard_layout", "azerty").lower() == "azerty"
    
    def get_movement_keys(self) -> Dict[str, str]:
        """Retourne les touches de mouvement selon le layout clavier."""
        keys = {"forward": "Z", "backward": "S", "left": "Q", "right": "D"}
        if not self.is_azerty_layout():
            keys.update({"forward": "W", "left": "A"})
        return keys
    
    def get_localized_text(self, key: str, default: str = "") -> str:
        """Retourne le texte localisé selon la langue configurée."""
        fr_texts = {
            "connecting": "Connexion au serveur...", "connected": "Connecté", "disconnected": "Déconnecté", 
            "connection_failed": "Échec de connexion", "blocks_visible": "Blocs visibles", "blocks_total": "Blocs total",
            "position": "Position", "fps": "FPS", "ping": "Ping", "players_online": "Joueurs en ligne",
            "flying": "Vol activé", "sprinting": "Course activée", "crouch": "Accroupi",
            "block_placed": "Bloc placé", "block_destroyed": "Bloc détruit", "inventory_full": "Inventaire plein",
            "server_error": "Erreur serveur", "reconnecting": "Reconnexion...", 
            "welcome": "Bienvenue sur le serveur Minecraft!", "controls_help": "Utilisez ZQSD pour vous déplacer"
        }
        
        en_texts = {
            "connecting": "Connecting to server...", "connected": "Connected", "disconnected": "Disconnected",
            "connection_failed": "Connection failed", "blocks_visible": "Blocks visible", "blocks_total": "Blocks total",
            "position": "Position", "fps": "FPS", "ping": "Ping", "players_online": "Players online",
            "flying": "Flying enabled", "sprinting": "Sprinting enabled", "crouch": "Crouching",
            "block_placed": "Block placed", "block_destroyed": "Block destroyed", "inventory_full": "Inventory full",
            "server_error": "Server error", "reconnecting": "Reconnecting...",
            "welcome": "Welcome to Minecraft server!", "controls_help": "Use WASD to move"
        }
        
        texts = fr_texts if self.get("interface", "language", "fr") == "fr" else en_texts
        return texts.get(key, default)


# Instance globale de configuration
config = ClientConfig()