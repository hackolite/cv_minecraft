"""
Network client for pyCraft-inspired architecture
Handles packet-based communication with the server
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Dict
from protocol.connection import Connection, ConnectionState
from protocol.packets import (
    PacketType, HandshakePacket, LoginRequestPacket, LoginResponsePacket,
    JoinGamePacket, PlayerPositionLookPacket, BlockChangePacket, 
    ChunkDataPacket, ChatMessagePacket, KeepAlivePacket
)
from protocol.auth import AuthManager


logger = logging.getLogger(__name__)


class NetworkClient:
    """
    Network client inspired by pyCraft architecture
    Handles all network communication with proper packet protocol
    """
    
    def __init__(self, username: str = "Player"):
        self.username = username
        self.connection: Optional[Connection] = None
        self.auth_manager = AuthManager(online_mode=False)
        
        # Connection info
        self.server_host = "localhost"
        self.server_port = 8766  # New protocol port
        
        # Player state
        self.player_uuid = ""
        self.entity_id = 0
        self.position = [0.0, 50.0, 0.0]
        self.rotation = [0.0, 0.0]
        
        # Game state
        self.world_loaded = False
        self.chunks: Dict[tuple, dict] = {}
        
        # Event callbacks
        self.on_login_success: Optional[Callable] = None
        self.on_world_update: Optional[Callable] = None
        self.on_block_change: Optional[Callable] = None
        self.on_chat_message: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        
        # Running state
        self.running = False
        self._network_task: Optional[asyncio.Task] = None
    
    async def connect(self, host: str = "localhost", port: int = 8766) -> bool:
        """Connect to the server"""
        self.server_host = host
        self.server_port = port
        
        try:
            logger.info(f"Connecting to {host}:{port}...")
            
            # Create connection
            self.connection = await Connection.create_client_connection(host, port)
            
            # Register packet handlers
            self._register_packet_handlers()
            
            # Start the handshake
            await self._perform_handshake()
            
            # Start network loop
            self.running = True
            self._network_task = asyncio.create_task(self.connection.start_packet_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    def _register_packet_handlers(self):
        """Register packet handlers"""
        self.connection.register_packet_handler(
            PacketType.LOGIN_RESPONSE, self._handle_login_response)
        self.connection.register_packet_handler(
            PacketType.JOIN_GAME, self._handle_join_game)
        self.connection.register_packet_handler(
            PacketType.CHUNK_DATA, self._handle_chunk_data)
        self.connection.register_packet_handler(
            PacketType.BLOCK_CHANGE, self._handle_block_change)
        self.connection.register_packet_handler(
            PacketType.CHAT_MESSAGE, self._handle_chat_message)
    
    async def _perform_handshake(self):
        """Perform the login handshake"""
        logger.info("Starting handshake...")
        
        # Send handshake packet
        handshake = HandshakePacket(
            protocol_version=1,
            server_address=self.server_host,
            server_port=self.server_port,
            next_state=ConnectionState.LOGIN
        )
        logger.info("Sending handshake packet...")
        await self.connection.send_packet(handshake)
        
        # Send login request
        session = self.auth_manager.create_session(self.username)
        login_request = LoginRequestPacket(
            username=self.username,
            uuid=session.uuid
        )
        logger.info("Sending login request...")
        await self.connection.send_packet(login_request)
        
        # Update connection state
        self.connection.state = ConnectionState.LOGIN
        logger.info("Handshake completed")
    
    async def _handle_login_response(self, packet: LoginResponsePacket):
        """Handle login response from server"""
        if packet.success:
            self.player_uuid = packet.player_uuid
            self.position = packet.spawn_position
            
            logger.info(f"Login successful as {self.username} ({self.player_uuid})")
            
            # Update connection state
            self.connection.state = ConnectionState.PLAY
            
            # Callback
            if self.on_login_success:
                self.on_login_success(self.username, self.player_uuid, self.position)
        else:
            logger.error(f"Login failed: {packet.message}")
            await self.disconnect()
    
    async def _handle_join_game(self, packet: JoinGamePacket):
        """Handle join game packet"""
        self.entity_id = packet.entity_id
        logger.info(f"Joined game with entity ID {self.entity_id}")
    
    async def _handle_chunk_data(self, packet: ChunkDataPacket):
        """Handle chunk data packet"""
        chunk_key = (packet.chunk_x, packet.chunk_z)
        self.chunks[chunk_key] = {
            'x': packet.chunk_x,
            'z': packet.chunk_z,
            'blocks': packet.blocks
        }
        
        logger.debug(f"Received chunk data for {chunk_key} with {len(packet.blocks)} blocks")
        
        # Callback for world update
        if self.on_world_update:
            self.on_world_update(packet.blocks)
    
    async def _handle_block_change(self, packet: BlockChangePacket):
        """Handle block change packet"""
        logger.debug(f"Block change at ({packet.x}, {packet.y}, {packet.z}): {packet.action} {packet.block_type}")
        
        # Callback for block change
        if self.on_block_change:
            self.on_block_change(packet.x, packet.y, packet.z, packet.block_type, packet.action)
    
    async def _handle_chat_message(self, packet: ChatMessagePacket):
        """Handle chat message packet"""
        logger.info(f"[{packet.sender}]: {packet.message}")
        
        # Callback for chat message
        if self.on_chat_message:
            self.on_chat_message(packet.sender, packet.message, packet.timestamp)
    
    async def send_position_update(self, x: float, y: float, z: float, 
                                 yaw: float = 0.0, pitch: float = 0.0, on_ground: bool = True):
        """Send player position update"""
        if not self.connection or self.connection.state != ConnectionState.PLAY:
            return
        
        self.position = [x, y, z]
        self.rotation = [yaw, pitch]
        
        packet = PlayerPositionLookPacket(x, y, z, yaw, pitch, on_ground)
        await self.connection.send_packet(packet)
    
    async def send_block_change(self, x: int, y: int, z: int, 
                              block_type: str, action: str = "place"):
        """Send block change request"""
        if not self.connection or self.connection.state != ConnectionState.PLAY:
            return
        
        packet = BlockChangePacket(x, y, z, block_type, action)
        await self.connection.send_packet(packet)
    
    async def send_chat_message(self, message: str):
        """Send chat message"""
        if not self.connection or self.connection.state != ConnectionState.PLAY:
            return
        
        packet = ChatMessagePacket(message, self.username)
        await self.connection.send_packet(packet)
    
    async def disconnect(self, reason: str = ""):
        """Disconnect from server"""
        self.running = False
        
        if self.connection:
            await self.connection.disconnect(reason)
        
        if self._network_task:
            self._network_task.cancel()
        
        # Callback
        if self.on_disconnect:
            self.on_disconnect(reason)
        
        logger.info(f"Disconnected: {reason}")
    
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return (self.connection and 
                self.connection.is_connected() and 
                self.connection.state == ConnectionState.PLAY)
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        if self.connection:
            stats = self.connection.get_stats()
            stats.update({
                'username': self.username,
                'player_uuid': self.player_uuid,
                'entity_id': self.entity_id,
                'position': self.position,
                'chunks_loaded': len(self.chunks)
            })
            return stats
        return {}