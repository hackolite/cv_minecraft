"""
Packet classes for Minecraft-like protocol
Inspired by pyCraft's packet architecture
"""

import json
import struct
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List
from enum import IntEnum


class PacketType(IntEnum):
    """Packet type identifiers"""
    # Authentication packets
    HANDSHAKE = 0x00
    LOGIN_REQUEST = 0x01
    LOGIN_RESPONSE = 0x02
    DISCONNECT = 0x03
    
    # World packets
    JOIN_GAME = 0x10
    WORLD_UPDATE = 0x11
    CHUNK_DATA = 0x12
    BLOCK_CHANGE = 0x13
    
    # Player packets
    PLAYER_POSITION = 0x20
    PLAYER_LOOK = 0x21
    PLAYER_POSITION_LOOK = 0x22
    PLAYER_ABILITIES = 0x23
    
    # Action packets
    PLAYER_DIGGING = 0x30
    PLAYER_BLOCK_PLACEMENT = 0x31
    HELD_ITEM_CHANGE = 0x32
    
    # Communication packets
    CHAT_MESSAGE = 0x40
    
    # Status packets
    KEEP_ALIVE = 0x50
    UPDATE_HEALTH = 0x51
    TIME_UPDATE = 0x52


class Packet(ABC):
    """Base packet class inspired by pyCraft"""
    
    packet_id: PacketType = None
    
    def __init__(self):
        self.timestamp = time.time()
    
    @abstractmethod
    def read(self, data: bytes) -> None:
        """Read packet data from bytes"""
        pass
    
    @abstractmethod
    def write(self) -> bytes:
        """Write packet data to bytes"""
        pass
    
    @classmethod
    def create_from_bytes(cls, packet_id: int, data: bytes) -> 'Packet':
        """Create packet instance from raw bytes"""
        packet_class = PACKET_REGISTRY.get(packet_id)
        if not packet_class:
            raise ValueError(f"Unknown packet ID: {packet_id}")
        
        packet = packet_class()
        packet.read(data)
        return packet
    
    def to_bytes(self) -> bytes:
        """Convert packet to bytes with header"""
        payload = self.write()
        packet_id = struct.pack('!H', self.packet_id)
        length = struct.pack('!I', len(payload))
        return length + packet_id + payload


class HandshakePacket(Packet):
    """Initial handshake packet"""
    packet_id = PacketType.HANDSHAKE
    
    def __init__(self, protocol_version: int = 1, server_address: str = "", 
                 server_port: int = 8765, next_state: int = 2):
        super().__init__()
        self.protocol_version = protocol_version
        self.server_address = server_address
        self.server_port = server_port
        self.next_state = next_state
    
    def read(self, data: bytes) -> None:
        offset = 0
        self.protocol_version = struct.unpack('!I', data[offset:offset+4])[0]
        offset += 4
        
        addr_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.server_address = data[offset:offset+addr_length].decode('utf-8')
        offset += addr_length
        
        self.server_port = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.next_state = struct.unpack('!I', data[offset:offset+4])[0]
    
    def write(self) -> bytes:
        data = struct.pack('!I', self.protocol_version)
        addr_bytes = self.server_address.encode('utf-8')
        data += struct.pack('!H', len(addr_bytes)) + addr_bytes
        data += struct.pack('!H', self.server_port)
        data += struct.pack('!I', self.next_state)
        return data


class LoginRequestPacket(Packet):
    """Login request packet"""
    packet_id = PacketType.LOGIN_REQUEST
    
    def __init__(self, username: str = "", uuid: str = ""):
        super().__init__()
        self.username = username
        self.uuid = uuid
    
    def read(self, data: bytes) -> None:
        offset = 0
        username_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.username = data[offset:offset+username_length].decode('utf-8')
        offset += username_length
        
        uuid_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.uuid = data[offset:offset+uuid_length].decode('utf-8')
    
    def write(self) -> bytes:
        username_bytes = self.username.encode('utf-8')
        uuid_bytes = self.uuid.encode('utf-8')
        
        data = struct.pack('!H', len(username_bytes)) + username_bytes
        data += struct.pack('!H', len(uuid_bytes)) + uuid_bytes
        return data


class LoginResponsePacket(Packet):
    """Login response packet"""
    packet_id = PacketType.LOGIN_RESPONSE
    
    def __init__(self, success: bool = False, message: str = "", 
                 player_uuid: str = "", spawn_position: List[float] = None):
        super().__init__()
        self.success = success
        self.message = message
        self.player_uuid = player_uuid
        self.spawn_position = spawn_position or [0.0, 50.0, 0.0]
    
    def read(self, data: bytes) -> None:
        offset = 0
        self.success = bool(struct.unpack('!B', data[offset:offset+1])[0])
        offset += 1
        
        message_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.message = data[offset:offset+message_length].decode('utf-8')
        offset += message_length
        
        uuid_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.player_uuid = data[offset:offset+uuid_length].decode('utf-8')
        offset += uuid_length
        
        self.spawn_position = list(struct.unpack('!fff', data[offset:offset+12]))
    
    def write(self) -> bytes:
        data = struct.pack('!B', int(self.success))
        
        message_bytes = self.message.encode('utf-8')
        data += struct.pack('!H', len(message_bytes)) + message_bytes
        
        uuid_bytes = self.player_uuid.encode('utf-8')
        data += struct.pack('!H', len(uuid_bytes)) + uuid_bytes
        
        data += struct.pack('!fff', *self.spawn_position)
        return data


class JoinGamePacket(Packet):
    """Join game packet with world info"""
    packet_id = PacketType.JOIN_GAME
    
    def __init__(self, entity_id: int = 0, gamemode: int = 1, 
                 dimension: int = 0, difficulty: int = 1, level_type: str = "default"):
        super().__init__()
        self.entity_id = entity_id
        self.gamemode = gamemode
        self.dimension = dimension
        self.difficulty = difficulty
        self.level_type = level_type
    
    def read(self, data: bytes) -> None:
        offset = 0
        self.entity_id = struct.unpack('!I', data[offset:offset+4])[0]
        offset += 4
        self.gamemode = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        self.dimension = struct.unpack('!i', data[offset:offset+4])[0]
        offset += 4
        self.difficulty = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        
        level_type_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.level_type = data[offset:offset+level_type_length].decode('utf-8')
    
    def write(self) -> bytes:
        data = struct.pack('!I', self.entity_id)
        data += struct.pack('!B', self.gamemode)
        data += struct.pack('!i', self.dimension)
        data += struct.pack('!B', self.difficulty)
        
        level_type_bytes = self.level_type.encode('utf-8')
        data += struct.pack('!H', len(level_type_bytes)) + level_type_bytes
        return data


class PlayerPositionLookPacket(Packet):
    """Player position and look packet"""
    packet_id = PacketType.PLAYER_POSITION_LOOK
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0,
                 yaw: float = 0.0, pitch: float = 0.0, on_ground: bool = True):
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground
    
    def read(self, data: bytes) -> None:
        self.x, self.y, self.z = struct.unpack('!fff', data[0:12])
        self.yaw, self.pitch = struct.unpack('!ff', data[12:20])
        self.on_ground = bool(struct.unpack('!B', data[20:21])[0])
    
    def write(self) -> bytes:
        data = struct.pack('!fff', self.x, self.y, self.z)
        data += struct.pack('!ff', self.yaw, self.pitch)
        data += struct.pack('!B', int(self.on_ground))
        return data


class BlockChangePacket(Packet):
    """Single block change packet"""
    packet_id = PacketType.BLOCK_CHANGE
    
    def __init__(self, x: int = 0, y: int = 0, z: int = 0, 
                 block_type: str = "", action: str = "place"):
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self.block_type = block_type
        self.action = action
    
    def read(self, data: bytes) -> None:
        offset = 0
        self.x, self.y, self.z = struct.unpack('!iii', data[offset:offset+12])
        offset += 12
        
        type_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.block_type = data[offset:offset+type_length].decode('utf-8')
        offset += type_length
        
        action_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.action = data[offset:offset+action_length].decode('utf-8')
    
    def write(self) -> bytes:
        data = struct.pack('!iii', self.x, self.y, self.z)
        
        type_bytes = self.block_type.encode('utf-8')
        data += struct.pack('!H', len(type_bytes)) + type_bytes
        
        action_bytes = self.action.encode('utf-8')
        data += struct.pack('!H', len(action_bytes)) + action_bytes
        return data


class ChunkDataPacket(Packet):
    """Chunk data packet for world updates"""
    packet_id = PacketType.CHUNK_DATA
    
    def __init__(self, chunk_x: int = 0, chunk_z: int = 0, blocks: List[Dict] = None):
        super().__init__()
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.blocks = blocks or []
    
    def read(self, data: bytes) -> None:
        offset = 0
        self.chunk_x, self.chunk_z = struct.unpack('!ii', data[offset:offset+8])
        offset += 8
        
        blocks_count = struct.unpack('!I', data[offset:offset+4])[0]
        offset += 4
        
        blocks_data_length = struct.unpack('!I', data[offset:offset+4])[0]
        offset += 4
        
        blocks_json = data[offset:offset+blocks_data_length].decode('utf-8')
        self.blocks = json.loads(blocks_json)
    
    def write(self) -> bytes:
        data = struct.pack('!ii', self.chunk_x, self.chunk_z)
        data += struct.pack('!I', len(self.blocks))
        
        blocks_json = json.dumps(self.blocks).encode('utf-8')
        data += struct.pack('!I', len(blocks_json)) + blocks_json
        return data


class ChatMessagePacket(Packet):
    """Chat message packet"""
    packet_id = PacketType.CHAT_MESSAGE
    
    def __init__(self, message: str = "", sender: str = "", timestamp: float = None):
        super().__init__()
        self.message = message
        self.sender = sender
        self.timestamp = timestamp or time.time()
    
    def read(self, data: bytes) -> None:
        offset = 0
        message_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.message = data[offset:offset+message_length].decode('utf-8')
        offset += message_length
        
        sender_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        self.sender = data[offset:offset+sender_length].decode('utf-8')
        offset += sender_length
        
        self.timestamp = struct.unpack('!d', data[offset:offset+8])[0]
    
    def write(self) -> bytes:
        message_bytes = self.message.encode('utf-8')
        sender_bytes = self.sender.encode('utf-8')
        
        data = struct.pack('!H', len(message_bytes)) + message_bytes
        data += struct.pack('!H', len(sender_bytes)) + sender_bytes
        data += struct.pack('!d', self.timestamp)
        return data


class KeepAlivePacket(Packet):
    """Keep alive packet for connection health"""
    packet_id = PacketType.KEEP_ALIVE
    
    def __init__(self, alive_id: int = 0):
        super().__init__()
        self.alive_id = alive_id
    
    def read(self, data: bytes) -> None:
        self.alive_id = struct.unpack('!I', data[0:4])[0]
    
    def write(self) -> bytes:
        return struct.pack('!I', self.alive_id)


class DisconnectPacket(Packet):
    """Disconnect packet"""
    packet_id = PacketType.DISCONNECT
    
    def __init__(self, reason: str = ""):
        super().__init__()
        self.reason = reason
    
    def read(self, data: bytes) -> None:
        reason_length = struct.unpack('!H', data[0:2])[0]
        self.reason = data[2:2+reason_length].decode('utf-8')
    
    def write(self) -> bytes:
        reason_bytes = self.reason.encode('utf-8')
        return struct.pack('!H', len(reason_bytes)) + reason_bytes


# Packet registry for dynamic packet creation
PACKET_REGISTRY: Dict[int, type] = {
    PacketType.HANDSHAKE: HandshakePacket,
    PacketType.LOGIN_REQUEST: LoginRequestPacket,
    PacketType.LOGIN_RESPONSE: LoginResponsePacket,
    PacketType.DISCONNECT: DisconnectPacket,
    PacketType.JOIN_GAME: JoinGamePacket,
    PacketType.CHUNK_DATA: ChunkDataPacket,
    PacketType.BLOCK_CHANGE: BlockChangePacket,
    PacketType.PLAYER_POSITION_LOOK: PlayerPositionLookPacket,
    PacketType.CHAT_MESSAGE: ChatMessagePacket,
    PacketType.KEEP_ALIVE: KeepAlivePacket,
}


def create_packet(packet_id: int, **kwargs) -> Packet:
    """Factory function to create packets"""
    packet_class = PACKET_REGISTRY.get(packet_id)
    if not packet_class:
        raise ValueError(f"Unknown packet ID: {packet_id}")
    
    return packet_class(**kwargs)