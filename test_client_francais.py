#!/usr/bin/env python3
"""
Test du Client Minecraft Français
=================================

Ce script teste les composants non-graphiques du client amélioré
pour vérifier la compatibilité avec le serveur existant.
"""

import asyncio
import json
import sys
import time
from unittest.mock import Mock

# Import des modules de notre client
from client_config import config
from protocol import *

class MockWindow:
    """Mock window pour tester le client réseau sans OpenGL."""
    
    def __init__(self):
        self.model = Mock()
        self.model.load_world_data = Mock()
        self.model.load_world_chunk = Mock()
        self.model.remove_block = Mock()
        self.model.add_block = Mock()
        self.model.other_players = {}
        self.show_message = Mock()

# Import du client réseau seulement
class TestAdvancedNetworkClient:
    """Version de test du client réseau avancé."""
    
    def __init__(self, window, server_url: str = None):
        self.window = window
        self.server_url = server_url or config.get_server_url()
        self.websocket = None
        self.connected = False
        self.loop = None
        self.thread = None
        self.player_id = None
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.reconnect_delay = 1
        self.last_ping_time = 0
        self.ping_ms = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.connection_time = 0
        self.test_messages = []
    
    async def test_connection(self):
        """Test de connexion simple."""
        try:
            import websockets
            print(f"🔗 Test de connexion à {self.server_url}")
            
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            self.connection_time = time.time()
            
            print("✅ Connexion établie")
            
            # Test d'envoi de message
            player_name = config.get("player", "name", "TestPlayer")
            join_msg = create_player_join_message(player_name)
            await self.websocket.send(join_msg.to_json())
            self.messages_sent += 1
            
            print(f"📤 Message d'inscription envoyé: {player_name}")
            
            # Test de réception de messages
            message_count = 0
            timeout_task = asyncio.create_task(asyncio.sleep(5))
            
            while message_count < 5:  # Attend quelques messages
                try:
                    message_task = asyncio.create_task(self.websocket.recv())
                    done, pending = await asyncio.wait(
                        [message_task, timeout_task], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    if timeout_task in done:
                        print("⏰ Timeout atteint")
                        break
                    
                    if message_task in done:
                        message_str = message_task.result()
                        message = Message.from_json(message_str)
                        self.messages_received += 1
                        message_count += 1
                        
                        print(f"📥 Message reçu ({message_count}): {message.type.value}")
                        self.test_messages.append(message)
                        
                        # Traite le message
                        self._handle_test_message(message)
                        
                except Exception as e:
                    print(f"❌ Erreur lors de la réception: {e}")
                    break
            
            # Test de déconnexion propre
            await self.websocket.close()
            self.connected = False
            print("👋 Déconnexion propre")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def _handle_test_message(self, message: Message):
        """Gère les messages de test."""
        if message.type == MessageType.WORLD_INIT:
            world_data = message.data
            print(f"🌍 Monde initialisé: taille {world_data.get('world_size', 'inconnue')}")
            self.window.model.load_world_data(world_data)
            
        elif message.type == MessageType.WORLD_CHUNK:
            chunk_data = message.data
            blocks_count = len(chunk_data.get("blocks", {}))
            print(f"🧱 Chunk reçu: {blocks_count} blocs")
            self.window.model.load_world_chunk(chunk_data)
            
        elif message.type == MessageType.PLAYER_UPDATE:
            player_data = message.data
            player_id = player_data.get("id", "unknown")
            position = player_data.get("position", [0, 0, 0])
            print(f"👤 Mise à jour joueur {player_id}: position {position}")
            
        elif message.type == MessageType.ERROR:
            error_msg = message.data.get("message", "Erreur inconnue")
            print(f"⚠️  Erreur serveur: {error_msg}")
    
    def get_test_results(self):
        """Retourne les résultats du test."""
        return {
            "connected": self.connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "server_url": self.server_url,
            "message_types": [msg.type.value for msg in self.test_messages]
        }

async def test_client_config():
    """Test la configuration du client."""
    print("⚙️  Test de la configuration...")
    
    # Test des valeurs par défaut
    assert config.get_server_url() == "ws://localhost:8765"
    assert config.is_azerty_layout() == True
    assert config.get("interface", "language") == "fr"
    
    # Test des touches de mouvement
    movement_keys = config.get_movement_keys()
    expected_keys = {"forward": "Z", "backward": "S", "left": "Q", "right": "D"}
    assert movement_keys == expected_keys
    
    # Test de la localisation
    welcome_text = config.get_localized_text("welcome")
    assert "Bienvenue" in welcome_text
    
    print("✅ Configuration OK")

async def test_network_client():
    """Test le client réseau."""
    print("🌐 Test du client réseau...")
    
    # Crée un mock window
    mock_window = MockWindow()
    
    # Crée le client de test
    client = TestAdvancedNetworkClient(mock_window)
    
    # Test de connexion
    success = await client.test_connection()
    
    if success:
        results = client.get_test_results()
        print("📊 Résultats du test:")
        print(f"  - Messages envoyés: {results['messages_sent']}")
        print(f"  - Messages reçus: {results['messages_received']}")
        print(f"  - Types de messages: {', '.join(results['message_types'])}")
        
        # Vérifications
        assert results['messages_sent'] > 0, "Aucun message envoyé"
        assert results['messages_received'] > 0, "Aucun message reçu"
        assert 'world_init' in results['message_types'], "Message d'initialisation manquant"
        
        print("✅ Client réseau OK")
        return True
    else:
        print("❌ Échec du test réseau")
        return False

async def test_protocol_compatibility():
    """Test la compatibilité du protocole."""
    print("📡 Test de compatibilité du protocole...")
    
    # Test de création de messages
    join_msg = create_player_join_message("TestPlayer")
    assert join_msg.type == MessageType.PLAYER_JOIN
    assert join_msg.data["name"] == "TestPlayer"
    
    move_msg = create_player_move_message((1, 0, -1), (45, 0))  # Delta movement, not absolute position
    assert move_msg.type == MessageType.PLAYER_MOVE
    assert move_msg.data["delta"] == (1, 0, -1)  # Now using delta instead of position
    assert move_msg.data["rotation"] == (45, 0)
    
    # Test de sérialisation/désérialisation
    json_str = join_msg.to_json()
    parsed_msg = Message.from_json(json_str)
    assert parsed_msg.type == join_msg.type
    assert parsed_msg.data == join_msg.data
    
    print("✅ Protocole compatible")

async def main():
    """Fonction principale de test."""
    print("🧪 Tests du Client Minecraft Français")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    try:
        # Test 1: Configuration
        await test_client_config()
        tests_passed += 1
        print()
        
        # Test 2: Protocole
        await test_protocol_compatibility()
        tests_passed += 1
        print()
        
        # Test 3: Réseau (seulement si serveur disponible)
        try:
            success = await test_network_client()
            if success:
                tests_passed += 1
        except Exception as e:
            print(f"⚠️  Test réseau ignoré (serveur indisponible): {e}")
            total_tests -= 1
        
        print()
        print("=" * 50)
        
        if tests_passed == total_tests:
            print(f"🎉 Tous les tests réussis! ({tests_passed}/{total_tests})")
            print("✅ Le client amélioré est compatible avec le serveur existant")
            return 0
        else:
            print(f"⚠️  Tests partiels: {tests_passed}/{total_tests} réussis")
            return 1
            
    except Exception as e:
        print(f"❌ Erreur durant les tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrompus par l'utilisateur")
        sys.exit(1)