"""
Configuration minimale du client Minecraft.
"""

import json
import os

class ClientConfig:
    """Gestionnaire de configuration minimal."""
    
    def __init__(self):
        self.config = {
            "server": {"host": "localhost", "port": 8765},
            "graphics": {"window_width": 1024, "window_height": 768},
            "controls": {"keyboard_layout": "azerty"}
        }
    
    def get(self, section: str, key: str = None, default=None):
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value) -> None:
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_server_url(self) -> str:
        host = self.get("server", "host", "localhost")
        port = self.get("server", "port", 8765)
        return f"ws://{host}:{port}"
    
    def save_config(self) -> None:
        pass  # Simplified - no saving

# Instance globale de configuration
config = ClientConfig()