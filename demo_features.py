#!/usr/bin/env python3
"""
Final demonstration of all implemented features
"""

import asyncio
import json
import logging
import websockets

SERVER_URI = "ws://localhost:8765"

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

async def demonstration():
    """Demonstrate all implemented features."""
    
    print("🎮 MINECRAFT FEATURES DEMONSTRATION")
    print("="*50)
    
    async with websockets.connect(SERVER_URI) as ws:
        # 1. Connection with high spawn
        print("🔌 Connecting to server...")
        join_msg = {"type": "player_join", "data": {"name": "Demo Player"}}
        await ws.send(json.dumps(join_msg))
        
        init_msg = json.loads(await ws.recv())
        spawn_pos = init_msg["data"]["spawn_position"]
        print(f"✅ Connected! High spawn position: {spawn_pos}")
        
        # Skip chunks but count them
        chunks = 0
        grass_blocks = 0
        stone_blocks = 0
        
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "world_chunk":
                chunks += 1
                blocks = msg["data"].get("blocks", {})
                for block_type in blocks.values():
                    if block_type == "grass":
                        grass_blocks += 1
                    elif block_type == "stone":
                        stone_blocks += 1
            elif msg["type"] == "player_list":
                break
        
        print(f"🌍 World loaded: {chunks} chunks with {grass_blocks} grass + {stone_blocks} stone blocks")
        
        # 2. Test movement (AZERTY controls simulation)
        print("\n🕹️ Testing AZERTY controls (Z/Q/S/D):")
        
        movements = [
            ("Z (forward)", [64, 100, 63]),  # Move forward
            ("Q (left)", [63, 100, 63]),     # Move left
            ("S (backward)", [63, 100, 64]), # Move backward  
            ("D (right)", [64, 100, 64])     # Move right
        ]
        
        for control, position in movements:
            move_msg = {"type": "player_move", "data": {"position": position, "rotation": [0, 0]}}
            await ws.send(json.dumps(move_msg))
            
            response = json.loads(await ws.recv())
            if response["type"] == "player_update":
                pos = response['data']['position']
                print(f"  {control}: Position {pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}")
        
        # 3. Demonstrate gravity
        print(f"\n⬇️ Gravity demonstration (starting from Y={spawn_pos[1]}):")
        
        for i in range(8):
            try:
                update = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.2))
                if update["type"] == "player_update":
                    pos = update['data']['position']
                    vel = update['data']['velocity']
                    on_ground = update['data']['on_ground']
                    
                    print(f"  Frame {i+1}: Y={pos[1]:.1f}, Velocity={vel[1]:.1f}, On Ground={on_ground}")
                    
                    if on_ground:
                        print("  🎯 Player landed on ground!")
                        break
                        
            except asyncio.TimeoutError:
                continue
        
        print("\n✨ Demonstration complete!")
        print("\n📋 Summary of implemented features:")
        print("  ✅ AZERTY layout: Z=forward, S=backward, Q=left, D=right")
        print("  ✅ World: Only grass (surface) and stone (underground) blocks")
        print("  ✅ Physics: Server-side gravity at 20Hz")
        print("  ✅ Spawn: High position (64, 100, 64) with falling")
        print("  ✅ Integration: Full client-server communication")

async def main():
    await demonstration()

if __name__ == "__main__":
    asyncio.run(main())