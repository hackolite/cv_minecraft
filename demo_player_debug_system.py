#!/usr/bin/env python3
"""
Demonstration script for the player position debug and broadcast system.
This script shows how the enhanced debug system works with multiple players.

Usage:
1. Start the server: python server.py
2. Run this demo: python demo_player_debug_system.py
"""

import asyncio
import websockets
import json
import time
import random

SERVER_URI = "ws://localhost:8765"

class PlayerDemo:
    """Represents a demo player with movement patterns."""
    
    def __init__(self, name, start_pos, color="🟦"):
        self.name = name
        self.position = list(start_pos)
        self.ws = None
        self.color = color
        self.movement_pattern = "random"
        
    async def connect(self):
        """Connect to server and join as player."""
        try:
            self.ws = await websockets.connect(SERVER_URI)
            print(f"{self.color} {self.name} connecting...")
            
            # Join
            join_msg = {"type": "player_join", "data": {"name": self.name}}
            await self.ws.send(json.dumps(join_msg))
            
            # Skip init messages
            msg_count = 0
            while msg_count < 70:
                msg = await self.ws.recv()
                data = json.loads(msg)
                msg_count += 1
                if data["type"] == "player_list":
                    print(f"{self.color} {self.name} connected successfully!")
                    break
                    
            return True
        except Exception as e:
            print(f"❌ {self.name} failed to connect: {e}")
            return False
    
    async def move_to(self, new_pos, rotation=[0, 0]):
        """Move to a specific position."""
        if not self.ws:
            return
            
        try:
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": new_pos,
                    "rotation": rotation
                }
            }
            await self.ws.send(json.dumps(move_msg))
            
            # Update local position
            old_pos = self.position.copy()
            self.position = new_pos.copy()
            
            distance = ((new_pos[0] - old_pos[0])**2 + 
                       (new_pos[1] - old_pos[1])**2 + 
                       (new_pos[2] - old_pos[2])**2)**0.5
            
            print(f"{self.color} {self.name} moved: {old_pos} → {new_pos} (distance: {distance:.1f})")
            
            # Drain any responses
            await asyncio.sleep(0.1)
            try:
                while True:
                    await asyncio.wait_for(self.ws.recv(), timeout=0.05)
            except asyncio.TimeoutError:
                pass
                
        except Exception as e:
            print(f"❌ {self.name} movement failed: {e}")
    
    async def random_walk(self, steps=5, step_size=3):
        """Perform random walk movements."""
        print(f"{self.color} {self.name} starting random walk...")
        
        for i in range(steps):
            # Small random movement
            dx = random.uniform(-step_size, step_size)
            dy = random.uniform(-1, 1)  # Small vertical movement
            dz = random.uniform(-step_size, step_size)
            
            new_pos = [
                self.position[0] + dx,
                max(15, self.position[1] + dy),  # Don't go below y=15
                self.position[2] + dz
            ]
            
            rotation = [random.uniform(0, 360), random.uniform(-30, 30)]
            
            await self.move_to(new_pos, rotation)
            await asyncio.sleep(0.8)  # Pause between moves
    
    async def circle_dance(self, radius=8, steps=8):
        """Move in a circle pattern."""
        print(f"{self.color} {self.name} dancing in a circle...")
        
        center = self.position.copy()
        for i in range(steps):
            angle = (i / steps) * 2 * 3.14159  # Full circle
            
            new_pos = [
                center[0] + radius * math.cos(angle),
                center[1],
                center[2] + radius * math.sin(angle)
            ]
            
            # Face the direction of movement
            rotation = [angle * 180 / 3.14159, 0]
            
            await self.move_to(new_pos, rotation)
            await asyncio.sleep(0.6)
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.ws:
            await self.ws.close()
            print(f"{self.color} {self.name} disconnected")

async def demo_debug_system():
    """Main demonstration of the debug system."""
    
    print("🎭 DEMONSTRATION DU SYSTÈME DE DEBUG DES POSITIONS")
    print("=" * 60)
    print("👀 Regardez les logs du serveur pour voir le debug en action!")
    print()
    
    # Create demo players
    players = [
        PlayerDemo("Alice", [64, 20, 64], "🔵"),
        PlayerDemo("Bob", [80, 20, 80], "🔴"), 
        PlayerDemo("Charlie", [50, 20, 50], "🟢")
    ]
    
    try:
        # Phase 1: Connect all players
        print("🔗 Phase 1: Connexion des joueurs...")
        for player in players:
            success = await player.connect()
            if not success:
                print(f"❌ Failed to connect {player.name}")
                return
            await asyncio.sleep(0.5)
        
        print("\n✅ Tous les joueurs connectés!")
        print("📊 Vérifiez le 'PLAYER DEBUG SUMMARY' dans les logs du serveur")
        await asyncio.sleep(3)
        
        # Phase 2: Individual movements
        print("\n🚶 Phase 2: Mouvements individuels...")
        print("🔍 Regardez les logs 'PLAYER_MOVE DEBUG' dans le serveur")
        
        # Alice moves first
        await players[0].move_to([69, 20, 64], [45, 0])
        await asyncio.sleep(1)
        
        # Bob moves  
        await players[1].move_to([85, 22, 75], [90, 10])
        await asyncio.sleep(1)
        
        # Charlie moves
        await players[2].move_to([45, 19, 55], [180, 0])
        await asyncio.sleep(2)
        
        # Phase 3: Simultaneous movements
        print("\n🌪️  Phase 3: Mouvements simultanés...")
        print("📡 Regardez les logs de broadcasting dans le serveur")
        
        # All players move at the same time
        moves = [
            players[0].move_to([75, 21, 70], [135, 5]),
            players[1].move_to([70, 20, 85], [225, -5]),
            players[2].move_to([60, 22, 60], [315, 10])
        ]
        await asyncio.gather(*moves)
        await asyncio.sleep(2)
        
        # Phase 4: Random movements
        print("\n🎲 Phase 4: Mouvements aléatoires...")
        print("⚡ Plusieurs mouvements rapides pour tester le système")
        
        # Each player does random movements
        random_moves = [
            players[0].random_walk(steps=4, step_size=4),
            players[1].random_walk(steps=4, step_size=3),
            players[2].random_walk(steps=4, step_size=5)
        ]
        await asyncio.gather(*random_moves)
        
        # Phase 5: Test anti-cheat
        print("\n🛡️  Phase 5: Test du système anti-cheat...")
        print("❌ Tentative de mouvement trop important (devrait être bloqué)")
        
        # Try an invalid movement (too large)
        current_pos = players[0].position
        invalid_pos = [current_pos[0] + 100, current_pos[1], current_pos[2]]  # Too far
        await players[0].move_to(invalid_pos, [0, 0])
        await asyncio.sleep(2)
        
        print("\n🎉 Démonstration terminée!")
        print("📋 Résumé de ce qui a été testé:")
        print("   ✅ Connexion multiple de joueurs")
        print("   ✅ Debug détaillé des mouvements individuels")
        print("   ✅ Broadcasting vers les autres joueurs")
        print("   ✅ Mouvements simultanés")
        print("   ✅ Résumé périodique des joueurs")
        print("   ✅ Système anti-cheat")
        print("\n📊 Vérifiez les logs du serveur pour voir tous les détails!")
        
    except Exception as e:
        print(f"❌ Erreur pendant la démonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect all players
        print("\n👋 Déconnexion des joueurs...")
        for player in players:
            await player.disconnect()

if __name__ == "__main__":
    import math  # For circle dance
    
    print("🎯 DEMO: Système de Debug des Positions de Joueurs")
    print("📝 Assurez-vous que le serveur tourne: python server.py")
    print("🚀 Démarrage de la démonstration...")
    print()
    
    try:
        asyncio.run(demo_debug_system())
    except KeyboardInterrupt:
        print("\n🛑 Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        print("💡 Assurez-vous que le serveur est démarré!")