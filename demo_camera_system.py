#!/usr/bin/env python3
"""
Démo du Système de Caméras - Demo Camera System
===============================================

Ce script démontre le système de caméras en:
1. Démarrant un serveur Minecraft
2. Créant un client qui place des blocs caméra
3. Vérifiant que les caméras sont créées avec leurs serveurs FastAPI
4. Testant les endpoints des caméras

Usage:
    python3 demo_camera_system.py
"""

import asyncio
import threading
import time
import requests
import json
import sys
from typing import Optional

from server import MinecraftServer
from minecraft_client import MinecraftClient
from camera_user_manager import camera_manager
from protocol import BlockType

# Configuration
SERVER_PORT = 8765
CLIENT_PORT = 8080
TEST_POSITIONS = [
    (50, 60, 50),
    (60, 60, 50),
    (50, 60, 60)
]

class CameraSystemDemo:
    def __init__(self):
        self.server: Optional[MinecraftServer] = None
        self.client: Optional[MinecraftClient] = None
        self.server_thread: Optional[threading.Thread] = None
        self.client_thread: Optional[threading.Thread] = None
        
    async def start_server(self):
        """Démarre le serveur Minecraft."""
        print("🚀 Démarrage du serveur Minecraft...")
        self.server = MinecraftServer()
        
        # Démarrer le serveur dans un thread séparé
        def run_server():
            asyncio.run(self.server.start_server(port=SERVER_PORT))
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Attendre que le serveur démarre
        await asyncio.sleep(2)
        print("✅ Serveur Minecraft démarré")
        
    def start_client(self):
        """Démarre le client Minecraft."""
        print("🎮 Démarrage du client Minecraft...")
        self.client = MinecraftClient(
            position=(45.0, 60.0, 45.0),
            block_type="STONE",
            server_host="localhost",
            server_port=CLIENT_PORT,
            enable_gui=False  # Mode headless pour la démo
        )
        
        # Démarrer le client dans un thread séparé
        def run_client():
            self.client.start_server()
            self.client.run()
        
        self.client_thread = threading.Thread(target=run_client, daemon=True)
        self.client_thread.start()
        
        # Attendre que le client démarre
        time.sleep(3)
        print("✅ Client Minecraft démarré")
        
    def place_camera_blocks(self):
        """Place des blocs caméra via l'API du client."""
        print("📹 Placement des blocs caméra...")
        client_url = f"http://localhost:{CLIENT_PORT}"
        
        for i, position in enumerate(TEST_POSITIONS):
            x, y, z = position
            try:
                response = requests.post(
                    f"{client_url}/place_block",
                    params={"x": x, "y": y, "z": z, "block_type": "CAMERA"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  ✅ Caméra {i+1} placée à {position}")
                else:
                    print(f"  ❌ Erreur placement caméra {i+1}: {response.status_code}")
                    print(f"     Response: {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Erreur placement caméra {i+1} à {position}: {e}")
                
        # Attendre que les caméras se créent
        print("⏳ Attente de la création des caméras...")
        time.sleep(3)
        
    def test_cameras(self):
        """Teste les caméras créées."""
        print("🔍 Test des caméras créées...")
        cameras = camera_manager.get_cameras()
        
        if not cameras:
            print("❌ Aucune caméra créée!")
            return False
            
        print(f"✅ {len(cameras)} caméra(s) créée(s)")
        
        success_count = 0
        for i, camera in enumerate(cameras):
            print(f"\n--- Test Caméra {i+1}: {camera['id']} ---")
            print(f"Position: {camera['position']}")
            print(f"Port: {camera['port']}")
            print(f"URL: {camera['url']}")
            print(f"État: {'actif' if camera['running'] else 'inactif'}")
            
            # Test de connectivité de base
            try:
                response = requests.get(camera['url'], timeout=5)
                if response.status_code == 200:
                    print("  ✅ Serveur FastAPI accessible")
                    success_count += 1
                    
                    # Test de l'endpoint de vue
                    try:
                        view_response = requests.get(camera['view_endpoint'], timeout=10)
                        if view_response.status_code == 200:
                            print(f"  ✅ Endpoint de vue accessible ({len(view_response.content)} bytes)")
                        else:
                            print(f"  ⚠️  Endpoint de vue: {view_response.status_code}")
                    except Exception as e:
                        print(f"  ⚠️  Erreur endpoint de vue: {e}")
                        
                else:
                    print(f"  ❌ Serveur non accessible: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Erreur de connexion: {e}")
                
        print(f"\n📊 Résultat: {success_count}/{len(cameras)} caméras fonctionnelles")
        return success_count > 0
        
    def cleanup_cameras(self):
        """Nettoie les caméras créées."""
        print("\n🧹 Nettoyage des caméras...")
        for position in TEST_POSITIONS:
            try:
                if camera_manager.remove_camera_user(position):
                    print(f"  ✅ Caméra supprimée à {position}")
                else:
                    print(f"  ⚠️  Aucune caméra trouvée à {position}")
            except Exception as e:
                print(f"  ❌ Erreur suppression caméra à {position}: {e}")
                
    async def run_demo(self):
        """Exécute la démo complète."""
        print("=" * 60)
        print("🎬 DÉMO DU SYSTÈME DE CAMÉRAS MINECRAFT")
        print("=" * 60)
        
        try:
            # 1. Démarrer le serveur
            await self.start_server()
            
            # 2. Démarrer le client
            self.start_client()
            
            # 3. Placer des blocs caméra
            self.place_camera_blocks()
            
            # 4. Tester les caméras
            cameras_working = self.test_cameras()
            
            if cameras_working:
                print("\n🎉 SUCCÈS: Le système de caméras fonctionne!")
                
                # Montrer comment utiliser le visualiseur
                print("\n📋 Pour visualiser les caméras:")
                print("   python3 camera_viewer.py --list")
                print("   python3 camera_viewer.py --position 50 60 50")
                print("   python3 camera_viewer.py --camera Camera_50_60_50")
                
            else:
                print("\n❌ ÉCHEC: Le système de caméras ne fonctionne pas correctement")
                return 1
                
        except KeyboardInterrupt:
            print("\n⏹️  Démo interrompue par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur lors de la démo: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            # 5. Nettoyer
            self.cleanup_cameras()
            
        return 0
        
def main():
    demo = CameraSystemDemo()
    return asyncio.run(demo.run_demo())

if __name__ == "__main__":
    sys.exit(main())