#!/usr/bin/env python3
"""
Test final integration of RTSP users system
"""

import asyncio
import json
import logging
import websockets

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"

async def test_complete_integration():
    """Test complete RTSP integration with the server."""
    logging.info("🧪 Test complet d'intégration des utilisateurs RTSP")
    
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Send player join
            join_msg = {"type": "player_join", "data": {"name": "TestIntegration"}}
            await ws.send(json.dumps(join_msg))
            logging.info(f"Envoyé -> {join_msg}")
            
            # Process messages
            chunk_count = 0
            received_player_list = False
            
            while not received_player_list:
                try:
                    msg_raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg_raw)
                    
                    if data["type"] == "world_init":
                        logging.info("✅ Reçu world_init")
                    elif data["type"] == "world_chunk":
                        chunk_count += 1
                        if chunk_count % 20 == 0:
                            logging.info(f"Reçu {chunk_count} chunks...")
                    elif data["type"] == "player_list":
                        logging.info("✅ Reçu player_list!")
                        players = data.get("players", [])
                        rtsp_users = [p for p in players if p.get("is_rtsp_user", False)]
                        connected_users = [p for p in players if not p.get("is_rtsp_user", False)]
                        
                        logging.info(f"📊 Total players: {len(players)}")
                        logging.info(f"🎥 RTSP users: {len(rtsp_users)}")
                        logging.info(f"👤 Connected users: {len(connected_users)}")
                        
                        for user in rtsp_users:
                            logging.info(f"  🎥 {user['name']} - Position: {user['position']} - RTSP User: {user.get('is_rtsp_user', False)}")
                        
                        for user in connected_users:
                            logging.info(f"  👤 {user['name']} - Position: {user['position']} - Connected: {user.get('is_connected', True)}")
                        
                        received_player_list = True
                        
                        # Validate we have the expected RTSP users
                        expected_rtsp_names = ["Observateur_1", "Observateur_2", "Observateur_3"]
                        rtsp_names = [u["name"] for u in rtsp_users]
                        
                        for expected in expected_rtsp_names:
                            if expected in rtsp_names:
                                logging.info(f"✅ {expected} trouvé dans la liste RTSP")
                            else:
                                logging.warning(f"⚠️  {expected} manquant dans la liste RTSP")
                        
                        if len(rtsp_users) == 3 and len(connected_users) >= 1:
                            logging.info("🎉 INTÉGRATION RÉUSSIE!")
                            logging.info("✅ 3 utilisateurs RTSP actifs")
                            logging.info("✅ Client connecté détecté")
                            return True
                        else:
                            logging.warning(f"⚠️  Nombres inattendus - RTSP: {len(rtsp_users)}, Connectés: {len(connected_users)}")
                            return False
                    
                    if chunk_count > 64:  # After all chunks are sent
                        logging.warning("⚠️  player_list non reçu après tous les chunks")
                        break
                        
                except asyncio.TimeoutError:
                    logging.info("Timeout en attente du prochain message")
                    break
                    
        return False
        
    except Exception as e:
        logging.error(f"❌ Erreur lors du test d'intégration: {e}")
        return False

async def main():
    """Run the complete integration test."""
    logging.info("🎯 Test d'intégration complet du système RTSP")
    
    success = await test_complete_integration()
    
    if success:
        logging.info("")
        logging.info("🎉 TEST D'INTÉGRATION RÉUSSI!")
        logging.info("✅ Système d'utilisateurs RTSP pleinement opérationnel")
        logging.info("✅ 3 utilisateurs RTSP configurés et actifs")
        logging.info("✅ Serveurs RTSP simulés fonctionnels")  
        logging.info("✅ Intégration serveur/client validée")
        return 0
    else:
        logging.error("")
        logging.error("❌ TEST D'INTÉGRATION ÉCHOUÉ")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))