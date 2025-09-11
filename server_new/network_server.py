"""
Network server with pyCraft-inspired packet handling
Handles client connections and packet-based communication
"""

import asyncio
import logging
import time
from typing import Dict, Set, Optional, List
from protocol.connection import Connection, ConnectionState
from protocol.packets import (
    PacketType, HandshakePacket, LoginRequestPacket, LoginResponsePacket,
    JoinGamePacket, PlayerPositionLookPacket, BlockChangePacket,
    ChunkDataPacket, ChatMessagePacket, KeepAlivePacket, DisconnectPacket
)
from protocol.auth import AuthManager, PlayerSession
from .world_manager import WorldManager
from .player_manager import PlayerManager, ServerPlayer


logger = logging.getLogger(__name__)


class NetworkServer:
    """
    Network server inspired by pyCraft architecture
    Handles packet-based communication with proper protocol
    """
    
    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        
        # Core components
        self.auth_manager = AuthManager(online_mode=False)
        self.world_manager = WorldManager()
        self.player_manager = PlayerManager()
        
        # Network state
        self.server: Optional[asyncio.Server] = None
        self.connections: Set[Connection] = set()
        self.player_connections: Dict[str, Connection] = {}  # UUID -> Connection
        
        # Server state
        self.running = False
        self.max_players = 20
        self.server_name = "Minecraft-like Server (pyCraft-inspired)"
        self.motd = "Welcome to the new architecture!"
        
        # Statistics
        self.total_connections = 0
        self.start_time = time.time()
        
        # Tasks
        self._server_task: Optional[asyncio.Task] = None
        self._world_update_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the server"""
        logger.info(f"Starting server on {self.host}:{self.port}")
        
        # Generate world
        await self.world_manager.generate_world(64)
        
        # Start server
        self.server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        
        self.running = True
        
        # Start background tasks
        self._world_update_task = asyncio.create_task(self._world_update_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"Server started on {self.host}:{self.port}")
        logger.info(f"Generated world with {self.world_manager.get_block_count()} blocks")
        
        # Serve forever
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """Stop the server"""
        logger.info("Stopping server")
        
        self.running = False
        
        # Stop tasks
        if self._world_update_task:
            self._world_update_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Disconnect all clients
        disconnect_tasks = []
        for connection in self.connections.copy():
            disconnect_tasks.append(connection.disconnect("Server shutting down"))
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection"""
        connection = await Connection.create_server_connection(reader, writer)
        self.connections.add(connection)
        self.total_connections += 1
        
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New client connected from {client_addr}")
        
        try:
            # Register packet handlers
            self._register_packet_handlers(connection)
            
            # Start packet loop
            await connection.start_packet_loop()
            
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            # Clean up connection
            self.connections.discard(connection)
            
            # Remove from player connections
            player_uuid = None
            for uuid, conn in self.player_connections.items():
                if conn == connection:
                    player_uuid = uuid
                    break
            
            if player_uuid:
                self.player_connections.pop(player_uuid, None)
                await self.player_manager.disconnect_player(player_uuid)
                logger.info(f"Player {player_uuid} disconnected")
    
    def _register_packet_handlers(self, connection: Connection):
        """Register packet handlers for a connection"""
        connection.register_packet_handler(PacketType.HANDSHAKE, 
                                         lambda p: self._handle_handshake(connection, p))
        connection.register_packet_handler(PacketType.LOGIN_REQUEST, 
                                         lambda p: self._handle_login_request(connection, p))
        connection.register_packet_handler(PacketType.PLAYER_POSITION_LOOK, 
                                         lambda p: self._handle_player_position(connection, p))
        connection.register_packet_handler(PacketType.BLOCK_CHANGE, 
                                         lambda p: self._handle_block_change(connection, p))
        connection.register_packet_handler(PacketType.CHAT_MESSAGE, 
                                         lambda p: self._handle_chat_message(connection, p))
        connection.register_packet_handler(PacketType.DISCONNECT, 
                                         lambda p: self._handle_disconnect(connection, p))
        connection.register_packet_handler(PacketType.KEEP_ALIVE, 
                                         lambda p: self._handle_keep_alive(connection, p))
    
    async def _handle_handshake(self, connection: Connection, packet: HandshakePacket):
        """Handle handshake packet"""
        logger.debug(f"Handshake: protocol={packet.protocol_version}, next_state={packet.next_state}")
        
        if packet.next_state == ConnectionState.LOGIN:
            connection.state = ConnectionState.LOGIN
        else:
            await connection.disconnect("Invalid handshake state")
    
    async def _handle_login_request(self, connection: Connection, packet: LoginRequestPacket):
        """Handle login request packet"""
        if connection.state != ConnectionState.LOGIN:
            await connection.disconnect("Invalid connection state for login")
            return
        
        logger.info(f"Login request from {packet.username}")
        
        # Check if server is full
        if len(self.player_connections) >= self.max_players:
            response = LoginResponsePacket(
                success=False,
                message="Server is full",
                player_uuid="",
                spawn_position=[0, 0, 0]
            )
            await connection.send_packet(response)
            await connection.disconnect("Server full")
            return
        
        # Authenticate player
        success, message, session = self.auth_manager.authenticate_player(packet.username)
        
        if success:
            # Create server player
            spawn_pos = [30.0, 50.0, 80.0]  # Default spawn
            player = await self.player_manager.create_player(
                session.uuid, session.username, spawn_pos
            )
            
            # Store connection
            self.player_connections[session.uuid] = connection
            
            # Send login response
            response = LoginResponsePacket(
                success=True,
                message="Login successful",
                player_uuid=session.uuid,
                spawn_position=spawn_pos
            )
            await connection.send_packet(response)
            
            # Send join game packet
            join_game = JoinGamePacket(
                entity_id=player.entity_id,
                gamemode=1,  # Creative
                dimension=0,
                difficulty=1,
                level_type="default"
            )
            await connection.send_packet(join_game)
            
            # Send initial world data
            await self._send_world_data(connection, player)
            
            # Update connection state
            connection.state = ConnectionState.PLAY
            
            logger.info(f"Player {packet.username} ({session.uuid}) joined the game")
            
        else:
            # Send failure response
            response = LoginResponsePacket(
                success=False,
                message=message,
                player_uuid="",
                spawn_position=[0, 0, 0]
            )
            await connection.send_packet(response)
            await connection.disconnect(message)
    
    async def _handle_player_position(self, connection: Connection, packet: PlayerPositionLookPacket):
        """Handle player position update"""
        if connection.state != ConnectionState.PLAY:
            return
        
        # Find player by connection
        player_uuid = None
        for uuid, conn in self.player_connections.items():
            if conn == connection:
                player_uuid = uuid
                break
        
        if not player_uuid:
            return
        
        # Update player position
        await self.player_manager.update_player_position(
            player_uuid, [packet.x, packet.y, packet.z], [packet.yaw, packet.pitch]
        )
    
    async def _handle_block_change(self, connection: Connection, packet: BlockChangePacket):
        """Handle block change request"""
        if connection.state != ConnectionState.PLAY:
            return
        
        # Find player by connection
        player_uuid = None
        for uuid, conn in self.player_connections.items():
            if conn == connection:
                player_uuid = uuid
                break
        
        if not player_uuid:
            return
        
        player = self.player_manager.get_player(player_uuid)
        if not player:
            return
        
        # Process block change
        position = (packet.x, packet.y, packet.z)
        
        if packet.action == "place":
            # Validate placement (basic check)
            if self.world_manager.can_place_block(position, player.position):
                self.world_manager.set_block(position, packet.block_type)
                
                # Broadcast to all players
                await self._broadcast_block_change(packet)
                
                logger.debug(f"Player {player.username} placed {packet.block_type} at {position}")
        
        elif packet.action == "remove":
            if self.world_manager.has_block(position):
                self.world_manager.remove_block(position)
                
                # Broadcast to all players
                await self._broadcast_block_change(packet)
                
                logger.debug(f"Player {player.username} removed block at {position}")
    
    async def _handle_chat_message(self, connection: Connection, packet: ChatMessagePacket):
        """Handle chat message"""
        if connection.state != ConnectionState.PLAY:
            return
        
        # Find player by connection
        player_uuid = None
        for uuid, conn in self.player_connections.items():
            if conn == connection:
                player_uuid = uuid
                break
        
        if not player_uuid:
            return
        
        player = self.player_manager.get_player(player_uuid)
        if not player:
            return
        
        logger.info(f"[{player.username}]: {packet.message}")
        
        # Broadcast chat message to all players
        chat_packet = ChatMessagePacket(
            message=packet.message,
            sender=player.username,
            timestamp=time.time()
        )
        
        await self._broadcast_packet(chat_packet)
    
    async def _handle_disconnect(self, connection: Connection, packet: DisconnectPacket):
        """Handle disconnect packet"""
        logger.info(f"Client requested disconnect: {packet.reason}")
        await connection.disconnect(packet.reason)
    
    async def _handle_keep_alive(self, connection: Connection, packet: KeepAlivePacket):
        """Handle keep alive packet"""
        # Keep alive is handled automatically by the connection class
        # We can add additional logic here if needed
        pass
    
    async def _send_world_data(self, connection: Connection, player: 'ServerPlayer'):
        """Send world data to a player"""
        # Get blocks near player
        blocks = self.world_manager.get_blocks_in_range(player.position, radius=50)
        
        # Convert to chunk data
        chunks = self.world_manager.blocks_to_chunks(blocks)
        
        # Send chunks
        for chunk_x, chunk_z, chunk_blocks in chunks:
            chunk_packet = ChunkDataPacket(chunk_x, chunk_z, chunk_blocks)
            await connection.send_packet(chunk_packet)
        
        logger.debug(f"Sent {len(chunks)} chunks to {player.username}")
    
    async def _broadcast_block_change(self, packet: BlockChangePacket):
        """Broadcast block change to all players"""
        await self._broadcast_packet(packet)
    
    async def _broadcast_packet(self, packet):
        """Broadcast a packet to all connected players"""
        if not self.player_connections:
            return
        
        send_tasks = []
        for connection in self.player_connections.values():
            if connection.is_connected():
                send_tasks.append(connection.send_packet(packet))
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
    
    async def _world_update_loop(self):
        """Periodic world updates"""
        while self.running:
            try:
                # Send player position updates
                await self._broadcast_player_updates()
                
                # Sleep for next update
                await asyncio.sleep(0.2)  # 5 updates per second
                
            except Exception as e:
                logger.error(f"Error in world update loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _broadcast_player_updates(self):
        """Broadcast player position updates"""
        if not self.player_connections:
            return
        
        # Get all player positions
        players_data = []
        for player_uuid in self.player_connections.keys():
            player = self.player_manager.get_player(player_uuid)
            if player:
                players_data.append({
                    'uuid': player.uuid,
                    'username': player.username,
                    'position': player.position,
                    'rotation': player.rotation
                })
        
        # Create position update packets for each player
        for player_uuid, connection in self.player_connections.items():
            if not connection.is_connected():
                continue
            
            # For now, we'll use chat messages to send player updates
            # In a full implementation, you'd have dedicated player update packets
            pass
    
    async def _cleanup_loop(self):
        """Periodic cleanup tasks"""
        while self.running:
            try:
                # Clean up expired sessions
                self.auth_manager.cleanup_expired_sessions()
                
                # Remove disconnected players
                await self.player_manager.cleanup_disconnected_players()
                
                # Sleep until next cleanup
                await asyncio.sleep(60.0)  # Every minute
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(10.0)
    
    def get_stats(self) -> dict:
        """Get server statistics"""
        uptime = time.time() - self.start_time
        return {
            'running': self.running,
            'uptime': uptime,
            'total_connections': self.total_connections,
            'current_players': len(self.player_connections),
            'max_players': self.max_players,
            'world_blocks': self.world_manager.get_block_count(),
            'host': self.host,
            'port': self.port
        }