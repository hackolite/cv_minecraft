#!/usr/bin/env python3
"""
Tests pour le client et serveur Minecraft-like
"""

import asyncio
import websockets
import json
import threading
import time
import sys
import os

# Ajouter le répertoire parent au chemin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_server_connection():
    """Test de connexion au serveur"""
    print("🧪 Test de connexion au serveur...")
    
    async def test_connection():
        try:
            # Tenter de se connecter
            uri = "ws://localhost:8765"
            websocket = await websockets.connect(uri)
            
            # Envoyer un message de test
            test_message = {
                "type": "join",
                "name": "TestClient"
            }
            await websocket.send(json.dumps(test_message))
            
            # Attendre une réponse
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            print(f"✅ Connexion réussie! Réponse: {response_data['type']}")
            
            await websocket.close()
            return True
            
        except ConnectionRefusedError:
            print("❌ Impossible de se connecter au serveur")
            print("🔧 Assurez-vous que le serveur est démarré (python3 server.py)")
            return False
        except asyncio.TimeoutError:
            print("❌ Timeout - le serveur ne répond pas")
            return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    return asyncio.run(test_connection())

def test_client_imports():
    """Test des imports du client"""
    print("🧪 Test des imports du client...")
    
    try:
        # Test des imports de base
        import ursina
        import websockets
        print("✅ Dépendances importées avec succès")
        
        # Test import du client
        from client import MinecraftClient
        print("✅ Client importé avec succès")
        
        # Test initialisation du client
        client = MinecraftClient()
        print("✅ Client initialisé avec succès")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        print("🔧 Installez les dépendances: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        return False

def main():
    """Tests principaux"""
    print("🎮 Tests Minecraft-like Client")
    print("=" * 30)
    
    # Test 1: Imports
    if not test_client_imports():
        return False
    
    print()
    
    # Test 2: Connexion serveur
    if not test_server_connection():
        print("\n🔧 Pour démarrer le serveur:")
        print("   python3 server.py")
        return False
    
    print("\n✅ Tous les tests sont passés!")
    print("🎮 Le client devrait fonctionner correctement")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)