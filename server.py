"""
Minecraft Server - Server-side game world and client connections
"""

import asyncio
import websockets
import uuid
from typing import Dict, Tuple, Optional, List, Any

from noise_gen import NoiseGen

SECTOR_SIZE = 16

# ---------- Protocol Definitions ----------

import json
from enum import Enum

class MessageType(Enum):
    # Client → Server
    PLAYER_JOIN = "player_join"
    PLAYER_MOVE = "player_move"  # maintenant avec delta
    PLAYER_LOOK = "player_look"
    BLOCK_PLACE = "block_place"
    BLOCK_DESTROY = "block_destroy"
    CHAT_MESSAGE = "chat_message"
    PLAYER_DISCONNECT = "player_disconnect"

    # Server → Client
    WORLD_INIT = "world_init"
    WORLD_CHUNK = "world_chunk"
    WORLD_UPDATE = "world_update"
    PLAYER_UPDATE = "player_update"
    BLOCK_UPDATE = "block_update"
    CHAT_BROADCAST = "chat_broadcast"
    PLAYER_LIST = "player_list"
    ERROR = "error"

class BlockType:
    GRASS = "grass"
    SAND = "sand"
    BRICK = "brick"
    STONE = "stone"
    WOOD = "wood"
    LEAF = "leaf"
    WATER = "water"
    AIR = "air"

class Message:
    def __init__(self, msg_type: MessageType, data: Dict[str, Any], player_id: Optional[str] = None):
        self.type = msg_type
        self.data = data
        self.player_id = player_id
        self.timestamp = None

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "player_id": self.player_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        msg_type = MessageType(data["type"])
        return cls(msg_type, data["data"], data.get("player_id"))

class PlayerState:
    def __init__(self, player_id: str, position: Tuple[float, float, float],
                 rotation: Tuple[float, float], name: Optional[str] = None):
        self.id = player_id
        self.position = position
        self.rotation = rotation
        self.name = name or f"Player_{player_id[:8]}"
        self.flying = False
        self.sprinting = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "position": self.position,
            "rotation": self.rotation,
            "name": self.name,
            "flying": self.flying,
            "sprinting": self.sprinting
        }

class BlockUpdate:
    def __init__(self, position: Tuple[int, int, int], block_type: str, player_id: Optional[str] = None):
        self.position = position
        self.block_type = block_type
        self.player_id = player_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "block_type": self.block_type,
            "player_id": self.player_id
        }

# ---------- Message creators ----------

def create_player_join_message(player_name: str) -> Message:
    return Message(MessageType.PLAYER_JOIN, {"name": player_name})

def create_world_init_message(world_data: Dict[str, Any]) -> Message:
    return Message(MessageType.WORLD_INIT, world_data)

def create_world_chunk_message(chunk_data: Dict[str, Any]) -> Message:
    return Message(MessageType.WORLD_CHUNK, chunk_data)

def create_world_update_message(blocks: List[BlockUpdate]) -> Message:
    return Message(MessageType.WORLD_UPDATE, {"blocks": [b.to_dict() for b in blocks]})

def create_player_list_message(players: List[PlayerState]) -> Message:
    return Message(MessageType.PLAYER_LIST, {"players": [p.to_dict() for p in players]})

# ---------- Utility functions ----------

def normalize(position):
    x, y, z = position
    return int(round(x)), int(round(y)), int(round(z))

def sectorize(position):
    x, y, z = normalize(position)
    return x // SECTOR_SIZE, 0, z // SECTOR_SIZE

# ---------- Game World ----------

class GameWorld:
    def __init__(self):
        self.world = {}       # position -> block type
        self.sectors = {}     # sector -> list of positions
        self._initialize_world()

    def _initialize_world(self):
        gen = NoiseGen(452692)
        n = 128
        s = 1
        height_map = [0] * (n * n)
        for x in range(0, n, s):
            for z in range(0, n, s):
                height_map[z + x * n] = int(gen.getHeight(x, z))

        for x in range(0, n, s):
            for z in range(0, n, s):
                h = height_map[z + x * n]
                if h < 15:
                    self.add_block((x, h, z), BlockType.SAND)
                    for y in range(h, 15):
                        self.add_block((x, y, z), BlockType.WATER)
                    continue
                self.add_block((x, h, z), BlockType.SAND if h < 18 else BlockType.GRASS)
                for y in range(h - 1, 0, -1):
                    self.add_block((x, y, z), BlockType.STONE)

    def add_block(self, position: Tuple[int, int, int], block_type: str) -> bool:
        if position in self.world:
            return False
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        return True

    def remove_block(self, position: Tuple[int, int, int]) -> bool:
        if position not in self.world or self.world[position] == BlockType.STONE:
            return False
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        return True

    def get_block(self, position: Tuple[int, int, int]) -> Optional[str]:
        return self.world.get(position)

    def get_world_data(self) -> Dict:
        return {"world_size": 128, "spawn_position": [30, 50, 80]}

    def get_world_chunk(self, chunk_x: int, chunk_z: int, chunk_size: int = 16) -> Dict:
        blocks = {}
        start_x, start_z = chunk_x * chunk_size, chunk_z * chunk_size
        end_x, end_z = start_x + chunk_size, start_z + chunk_size
        for pos, block_type in self.world.items():
            x, y, z = pos
            if start_x <= x < end_x and start_z <= z < end_z:
                blocks[f"{x},{y},{z}"] = block_type
        return {"chunk_x": chunk_x, "chunk_z": chunk_z, "blocks": blocks}

# ---------- Minecraft Server ----------

class MinecraftServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.world = GameWorld()
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.players: Dict[str, PlayerState] = {}
        self.running = False

    async def register_client(self, websocket):
        player_id = str(uuid.uuid4())
        self.clients[player_id] = websocket
        self.players[player_id] = PlayerState(player_id, (30,50,80), (0,0))
        print(f"Player {player_id} connected")
        return player_id

    async def unregister_client(self, player_id):
        self.clients.pop(player_id, None)
        self.players.pop(player_id, None)
        await self.broadcast_player_list()
        print(f"Player {player_id} disconnected")

    async def broadcast_message(self, message: Message, exclude_player: Optional[str] = None):
        if not self.clients:
            return
        json_msg = message.to_json()
        disconnected = []
        for pid, ws in list(self.clients.items()):
            if exclude_player == pid:
                continue
            try:
                await ws.send(json_msg)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(pid)
        for pid in disconnected:
            await self.unregister_client(pid)

    async def send_to_client(self, player_id: str, message: Message):
        if player_id not in self.clients:
            return
        try:
            await self.clients[player_id].send(message.to_json())
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(player_id)

    async def broadcast_player_list(self):
        message = create_player_list_message(list(self.players.values()))
        await self.broadcast_message(message)

    async def handle_client_message(self, player_id: str, message: Message):
        if message.type == MessageType.PLAYER_JOIN:
            self.players[player_id].name = message.data.get("name", f"Player_{player_id[:8]}")
            await self.send_to_client(player_id, create_world_init_message(self.world.get_world_data()))
            chunk_size = 16
            for cx in range(128 // chunk_size):
                for cz in range(128 // chunk_size):
                    chunk = self.world.get_world_chunk(cx, cz, chunk_size)
                    if chunk["blocks"]:
                        await self.send_to_client(player_id, create_world_chunk_message(chunk))
            await self.broadcast_player_list()

        elif message.type == MessageType.PLAYER_MOVE and player_id in self.players:
            # On reçoit un delta
            p = self.players[player_id]
            dx, dy, dz = message.data["delta"]
            x, y, z = p.position
            p.position = (x + dx, y + dy, z + dz)
            p.rotation = tuple(message.data["rotation"])

            # Broadcast aux autres joueurs
            await self.broadcast_message(Message(MessageType.PLAYER_UPDATE, p.to_dict()), exclude_player=player_id)

            # Renvoyer la position recalculée au joueur
            await self.send_to_client(player_id, Message(MessageType.PLAYER_UPDATE, p.to_dict()))

        elif message.type == MessageType.BLOCK_PLACE:
            pos = tuple(message.data["position"])
            block_type = message.data["block_type"]
            if self.world.add_block(pos, block_type):
                await self.broadcast_message(create_world_update_message([BlockUpdate(pos, block_type, player_id)]))

        elif message.type == MessageType.BLOCK_DESTROY:
            pos = tuple(message.data["position"])
            if self.world.remove_block(pos):
                await self.broadcast_message(create_world_update_message([BlockUpdate(pos, BlockType.AIR, player_id)]))

        elif message.type == MessageType.CHAT_MESSAGE:
            name = self.players[player_id].name if player_id in self.players else "Unknown"
            await self.broadcast_message(Message(MessageType.CHAT_BROADCAST, {"text": f"{name}: {message.data['text']}"}))

    async def handle_client(self, websocket, path):
        player_id = await self.register_client(websocket)
        try:
            async for msg_str in websocket:
                try:
                    msg = Message.from_json(msg_str)
                    msg.player_id = player_id
                    await self.handle_client_message(player_id, msg)
                except Exception as e:
                    print(f"Error from {player_id}: {e}")
                    await self.send_to_client(player_id, Message(MessageType.ERROR, {"message": str(e)}))
        finally:
            await self.unregister_client(player_id)

    async def start_server(self):
        self.running = True
        print(f"Server starting on {self.host}:{self.port}")
        server = await websockets.serve(self.handle_client, self.host, self.port)
        await server.wait_closed()

    def stop_server(self):
        self.running = False

def main():
    server = MinecraftServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        server.stop_server()
        print("Server stopped")

if __name__ == "__main__":
    main()
