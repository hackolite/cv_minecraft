"""
Connection management inspired by pyCraft
Handles packet-based communication over TCP sockets
"""

import asyncio
import struct
import logging
import time
from typing import Optional, Callable, Dict, Any
from .packets import Packet, PacketType, PACKET_REGISTRY, DisconnectPacket, KeepAlivePacket


logger = logging.getLogger(__name__)


class ConnectionState:
    """Connection state enum"""
    HANDSHAKING = 0
    STATUS = 1
    LOGIN = 2
    PLAY = 3
    DISCONNECTED = 4


class Connection:
    """
    Connection class inspired by pyCraft's architecture
    Handles packet-based communication with proper framing
    """
    
    def __init__(self, reader: asyncio.StreamReader = None, 
                 writer: asyncio.StreamWriter = None):
        self.reader = reader
        self.writer = writer
        self.state = ConnectionState.HANDSHAKING
        self.compression_enabled = False
        self.compression_threshold = 256
        
        # Connection health
        self.last_keep_alive = time.time()
        self.keep_alive_interval = 30.0
        self.timeout = 60.0
        
        # Packet handlers
        self.packet_handlers: Dict[PacketType, Callable] = {}
        
        # Statistics
        self.packets_sent = 0
        self.packets_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        
        # Running state
        self.running = False
        self._keep_alive_task = None
    
    @classmethod
    async def create_client_connection(cls, host: str, port: int) -> 'Connection':
        """Create a client connection to a server"""
        try:
            reader, writer = await asyncio.open_connection(host, port)
            connection = cls(reader, writer)
            logger.info(f"Connected to {host}:{port}")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to {host}:{port}: {e}")
            raise
    
    @classmethod
    async def create_server_connection(cls, reader: asyncio.StreamReader, 
                                     writer: asyncio.StreamWriter) -> 'Connection':
        """Create a server-side connection from client"""
        connection = cls(reader, writer)
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New client connection from {client_addr}")
        return connection
    
    def register_packet_handler(self, packet_type: PacketType, handler: Callable):
        """Register a packet handler for a specific packet type"""
        self.packet_handlers[packet_type] = handler
    
    async def send_packet(self, packet: Packet) -> None:
        """Send a packet over the connection"""
        if not self.writer:
            raise ConnectionError("Connection not established")
        
        try:
            packet_data = packet.to_bytes()
            logger.debug(f"Sending packet {packet.packet_id} with {len(packet_data)} bytes: {packet_data}")
            
            self.writer.write(packet_data)
            await self.writer.drain()  # Ensure data is sent
            
            # Small delay to ensure packet is fully transmitted
            await asyncio.sleep(0.01)
            
            self.packets_sent += 1
            self.bytes_sent += len(packet_data)
            
            logger.debug(f"Sent packet {packet.packet_id} ({len(packet_data)} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to send packet {packet.packet_id}: {e}")
            raise
    
    async def read_packet(self) -> Optional[Packet]:
        """Read a packet from the connection"""
        if not self.reader:
            return None
        
        try:
            # Read packet length (4 bytes)
            logger.debug("Reading packet length...")
            length_data = await self.reader.readexactly(4)
            if not length_data:
                logger.debug("No length data received")
                return None
            
            packet_length = struct.unpack('!I', length_data)[0]
            logger.debug(f"Packet length: {packet_length}")
            logger.debug(f"Raw length bytes: {length_data}")
            
            # Validate packet length
            if packet_length < 2 or packet_length > 65536:  # Reasonable limits
                logger.error(f"Invalid packet length: {packet_length}")
                return None
            
            # Read the entire packet data (packet ID + payload)
            logger.debug(f"Reading full packet data of {packet_length} bytes...")
            packet_data = await self.reader.readexactly(packet_length)
            logger.debug(f"Raw packet data: {packet_data}")
            
            # Extract packet ID (first 2 bytes)
            packet_id = struct.unpack('!H', packet_data[0:2])[0]
            logger.debug(f"Packet ID: {packet_id}")
            
            # Extract payload (remaining bytes)
            payload = packet_data[2:]
            logger.debug(f"Payload length: {len(payload)}")
            logger.debug(f"Raw payload bytes: {payload}")
            
            # Create packet from registry
            packet_class = PACKET_REGISTRY.get(packet_id)
            if not packet_class:
                logger.warning(f"Unknown packet ID: {packet_id} (length: {packet_length})")
                # Skip unknown packet but don't fail
                return None
            
            packet = packet_class()
            if payload:
                logger.debug(f"Parsing payload for packet {packet_id}")
                try:
                    packet.read(payload)
                except Exception as parse_error:
                    logger.error(f"Failed to parse packet {packet_id}: {parse_error}")
                    logger.error(f"Payload was: {payload}")
                    raise
            
            self.packets_received += 1
            self.bytes_received += len(length_data) + len(packet_data)
            
            logger.debug(f"Successfully received packet {packet_id} ({packet_length} bytes)")
            
            return packet
            
        except asyncio.IncompleteReadError as e:
            logger.info(f"Connection closed by peer: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read packet: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't raise, just return None to close connection gracefully
            return None
    
    async def start_packet_loop(self) -> None:
        """Start the main packet handling loop"""
        self.running = True
        self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
        
        try:
            while self.running:
                packet = await self.read_packet()
                if packet is None:
                    break
                
                await self._handle_packet(packet)
                
        except Exception as e:
            logger.error(f"Packet loop error: {e}")
        finally:
            await self.disconnect("Connection closed")
    
    async def _handle_packet(self, packet: Packet) -> None:
        """Handle a received packet"""
        # Update keep alive
        if isinstance(packet, KeepAlivePacket):
            self.last_keep_alive = time.time()
            # Echo back keep alive
            await self.send_packet(KeepAlivePacket(packet.alive_id))
            return
        
        # Call registered handler
        handler = self.packet_handlers.get(packet.packet_id)
        if handler:
            try:
                await handler(packet)
            except Exception as e:
                logger.error(f"Error in packet handler for {packet.packet_id}: {e}")
        else:
            logger.warning(f"No handler registered for packet {packet.packet_id}")
    
    async def _keep_alive_loop(self) -> None:
        """Send periodic keep alive packets"""
        keep_alive_id = 0
        
        while self.running:
            try:
                await asyncio.sleep(self.keep_alive_interval)
                
                if not self.running:
                    break
                
                # Check if we've received a keep alive recently
                time_since_last = time.time() - self.last_keep_alive
                if time_since_last > self.timeout:
                    logger.warning("Keep alive timeout, disconnecting")
                    await self.disconnect("Keep alive timeout")
                    break
                
                # Send keep alive
                keep_alive_id += 1
                await self.send_packet(KeepAlivePacket(keep_alive_id))
                
            except Exception as e:
                logger.error(f"Keep alive error: {e}")
                break
    
    async def disconnect(self, reason: str = "") -> None:
        """Disconnect the connection"""
        if not self.running:
            return
        
        self.running = False
        self.state = ConnectionState.DISCONNECTED
        
        logger.info(f"Disconnecting: {reason}")
        
        # Cancel keep alive task
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
        
        # Send disconnect packet if possible
        try:
            if self.writer:
                await self.send_packet(DisconnectPacket(reason))
        except:
            pass  # Ignore errors during disconnect
        
        # Close writer
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except:
                pass  # Ignore errors during close
        
        logger.info("Connection closed")
    
    def is_connected(self) -> bool:
        """Check if the connection is active"""
        return (self.running and 
                self.writer and 
                not self.writer.is_closing() and
                self.state != ConnectionState.DISCONNECTED)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "state": self.state,
            "connected": self.is_connected(),
            "last_keep_alive": self.last_keep_alive
        }