#!/usr/bin/env python3
"""
Demonstration of the complete server-side collision management system.

This script shows how the new system works:
1. Client sends movement requests to server
2. Server validates movement with simple collision detection
3. Server responds with 'ok' or 'forbidden' status
4. Client applies server position and shows warnings for forbidden moves
"""

import asyncio
import json
import websockets
import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import MinecraftServer

async def demo_collision_system():
    """Demonstrate the complete server-side collision management workflow."""
    
    print("🎮 DÉMONSTRATION: Gestion des collisions côté serveur")
    print("=" * 60)
    
    # Start server
    server = MinecraftServer(host='localhost', port=8768)
    server_task = asyncio.create_task(server.start_server())
    
    # Wait for server to start
    await asyncio.sleep(0.5)
    
    try:
        print("\n📡 Connexion au serveur...")
        uri = "ws://localhost:8768"
        async with websockets.connect(uri) as websocket:
            
            # Join as player
            join_msg = {"type": "player_join", "data": {"name": "DemoPlayer"}}
            await websocket.send(json.dumps(join_msg))
            print("👤 Joueur connecté")
            
            # Receive world_init
            response = json.loads(await websocket.recv())
            spawn_position = response.get("spawn_position", [64, 100, 64])
            print(f"🌍 Position de spawn: {spawn_position}")
            
            # Skip chunks until player_list
            while True:
                msg = json.loads(await websocket.recv())
                if msg["type"] == "player_list":
                    break
            
            print("\n" + "="*60)
            print("🧪 TEST 1: Mouvement valide")
            print("="*60)
            
            # Valid movement
            valid_pos = [spawn_position[0] + 2, spawn_position[1], spawn_position[2] + 1]
            print(f"📤 CLIENT: Demande de mouvement vers {valid_pos}")
            
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": valid_pos,
                    "rotation": [45, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            response = json.loads(await websocket.recv())
            print(f"📥 SERVEUR: {response['data']['status'].upper()}")
            print(f"📍 Position confirmée: {response['data']['position']}")
            
            if response['data']['status'] == 'ok':
                print("✅ Mouvement accepté - aucune collision détectée")
            
            print("\n" + "="*60)
            print("🧪 TEST 2: Mouvement avec collision (anti-cheat)")
            print("="*60)
            
            # Large movement (anti-cheat)
            large_pos = [spawn_position[0] + 200, spawn_position[1], spawn_position[2]]
            print(f"📤 CLIENT: Tentative de téléportation vers {large_pos}")
            
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": large_pos,
                    "rotation": [90, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            response = json.loads(await websocket.recv())
            print(f"📥 SERVEUR: {response['data']['status'].upper()}")
            print(f"📍 Position maintenue: {response['data']['position']}")
            
            if response['data']['status'] == 'forbidden':
                print("🚫 Mouvement interdit - distance trop importante (anti-cheat)")
                print("⚠️  CLIENT afficherait: 'Mouvement bloqué par le serveur - collision détectée'")
            
            print("\n" + "="*60)
            print("🧪 TEST 3: Collision avec un bloc")
            print("="*60)
            
            # Collision with block
            collision_pos = [64, 0, 64]  # Underground position
            print(f"📤 CLIENT: Tentative de mouvement vers {collision_pos} (sous terre)")
            
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": collision_pos,
                    "rotation": [0, -90]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            response = json.loads(await websocket.recv())
            print(f"📥 SERVEUR: {response['data']['status'].upper()}")
            print(f"📍 Position maintenue: {response['data']['position']}")
            
            if response['data']['status'] == 'forbidden':
                print("🚫 Mouvement interdit - collision avec bloc détectée")
                print("⚠️  CLIENT afficherait: 'Mouvement bloqué par le serveur - collision détectée'")
            
            print("\n" + "="*60)
            print("📋 RÉSUMÉ DU SYSTÈME")
            print("="*60)
            print("🔹 Le CLIENT envoie les intentions de mouvement au serveur")
            print("🔹 Le SERVEUR valide avec une détection de collision simple:")
            print("   • Vérification anti-cheat (distance de mouvement)")
            print("   • Collision avec blocs (centre du joueur dans un bloc solide)")
            print("   • Collision avec autres joueurs")
            print("🔹 Le SERVEUR répond avec 'ok' ou 'forbidden' + position")
            print("🔹 Le CLIENT applique la position du serveur sans correction locale")
            print("🔹 Le CLIENT affiche un avertissement en cas de 'forbidden'")
            print("🔹 Aucun calcul de snapping côté client")
            print("\n✅ Système de collision côté serveur opérationnel!")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop server
        server.running = False
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(demo_collision_system())