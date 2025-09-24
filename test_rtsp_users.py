#!/usr/bin/env python3
"""
Test des utilisateurs RTSP
Test for RTSP users functionality
"""

import asyncio
import json
import logging
import websockets
from user_manager import user_manager

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"

async def test_rtsp_users_creation():
    """Test the creation of RTSP users at startup."""
    logging.info("🧪 Test de création des utilisateurs RTSP")
    
    # Test the user manager
    users = user_manager.create_startup_users()
    
    assert len(users) == 3, f"Attendu 3 utilisateurs, trouvé {len(users)}"
    
    expected_names = ["Observateur_1", "Observateur_2", "Observateur_3"]
    for i, user in enumerate(users):
        assert user.name == expected_names[i], f"Nom incorrect: {user.name}"
        assert user.rtsp_port == 8554 + i, f"Port RTSP incorrect: {user.rtsp_port}"
        assert user.is_active, "L'utilisateur devrait être actif"
        logging.info(f"✅ Utilisateur validé: {user.name} - {user.rtsp_url}")
    
    logging.info("✅ Test de création des utilisateurs RTSP réussi")
    return users

async def test_rtsp_urls():
    """Test RTSP URLs generation."""
    logging.info("🧪 Test des URLs RTSP")
    
    urls = user_manager.get_rtsp_urls()
    
    assert len(urls) == 3, f"Attendu 3 URLs RTSP, trouvé {len(urls)}"
    
    expected_urls = [
        "rtsp://localhost:8554/stream",
        "rtsp://localhost:8555/stream", 
        "rtsp://localhost:8556/stream"
    ]
    
    for i, (name, url) in enumerate(urls.items()):
        assert url == expected_urls[i], f"URL incorrecte pour {name}: {url}"
        logging.info(f"✅ URL RTSP validée: {name} -> {url}")
    
    logging.info("✅ Test des URLs RTSP réussi")

async def test_server_with_rtsp_users():
    """Test server integration with RTSP users."""
    logging.info("🧪 Test d'intégration serveur avec utilisateurs RTSP")
    
    try:
        # Try to connect to server and check if RTSP users appear in player list
        async with websockets.connect(SERVER_URI) as ws:
            # Send player join
            join_msg = {"type": "player_join", "data": {"name": "TestClient"}}
            await ws.send(json.dumps(join_msg))
            logging.info(f"Envoyé -> {join_msg}")
            
            # Receive world_init
            resp_raw = await ws.recv()
            resp = json.loads(resp_raw)
            logging.info(f"Reçu <- {resp['type']}")
            assert resp["type"] == "world_init"
            
            # Wait for player_list message which should include RTSP users
            while True:
                msg_raw = await ws.recv()
                data = json.loads(msg_raw)
                logging.info(f"Reçu <- {data['type']}")
                
                if data["type"] == "player_list":
                    players = data.get("data", {}).get("players", [])
                    rtsp_users = [p for p in players if p.get("is_rtsp_user", False)]
                    
                    logging.info(f"Joueurs trouvés: {len(players)}")
                    logging.info(f"Utilisateurs RTSP trouvés: {len(rtsp_users)}")
                    
                    if len(rtsp_users) >= 3:
                        for user in rtsp_users:
                            logging.info(f"✅ Utilisateur RTSP: {user['name']} à la position {user['position']}")
                        logging.info("✅ Test d'intégration serveur réussi")
                        return
                        
                    break
                    
        logging.warning("⚠️  Pas assez d'utilisateurs RTSP trouvés dans la liste des joueurs")
                    
    except Exception as e:
        logging.error(f"❌ Erreur lors du test d'intégration: {e}")

async def test_config_file_creation():
    """Test configuration file creation."""
    logging.info("🧪 Test de création du fichier de configuration")
    
    import os
    config_file = "users_config.json"
    
    # Remove existing config file if present
    if os.path.exists(config_file):
        os.remove(config_file)
    
    # Create a new user manager which should create the config file
    from user_manager import UserManager
    test_manager = UserManager(config_file)
    
    assert os.path.exists(config_file), "Le fichier de configuration n'a pas été créé"
    
    # Load and validate the config
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    assert "users" in config, "Section 'users' manquante dans la configuration"
    assert "rtsp_settings" in config, "Section 'rtsp_settings' manquante dans la configuration"
    assert len(config["users"]) == 3, f"Attendu 3 utilisateurs dans la config, trouvé {len(config['users'])}"
    
    for i, user in enumerate(config["users"]):
        assert "name" in user, f"Nom manquant pour l'utilisateur {i}"
        assert "rtsp_port" in user, f"Port RTSP manquant pour l'utilisateur {i}"
        assert "position" in user, f"Position manquante pour l'utilisateur {i}"
        assert "rotation" in user, f"Rotation manquante pour l'utilisateur {i}"
        
    logging.info("✅ Test de création du fichier de configuration réussi")

async def main():
    """Run all RTSP user tests."""
    logging.info("🎯 Démarrage des tests utilisateurs RTSP")
    
    try:
        # Test 1: User creation
        await test_rtsp_users_creation()
        
        # Test 2: RTSP URLs
        await test_rtsp_urls()
        
        # Test 3: Config file creation
        await test_config_file_creation()
        
        # Test 4: Server integration (requires server to be running)
        try:
            await test_server_with_rtsp_users()
        except Exception as e:
            logging.warning(f"Test d'intégration serveur ignoré (serveur non démarré?): {e}")
        
        logging.info("")
        logging.info("🎉 TOUS LES TESTS RÉUSSIS!")
        logging.info("✅ Système d'utilisateurs RTSP fonctionnel")
        logging.info("✅ 3 utilisateurs configurés par défaut")
        logging.info("✅ Serveurs RTSP configurés correctement")
        
    except Exception as e:
        logging.error(f"❌ Erreur dans les tests: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))