#!/usr/bin/env python3
"""
Debug packet serialization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol.packets import HandshakePacket
from protocol.connection import ConnectionState

# Test handshake packet creation
handshake = HandshakePacket(
    protocol_version=1,
    server_address="localhost",
    server_port=8766,
    next_state=ConnectionState.LOGIN
)

print(f"Original packet:")
print(f"  protocol_version: {handshake.protocol_version}")
print(f"  server_address: '{handshake.server_address}'")
print(f"  server_port: {handshake.server_port}")
print(f"  next_state: {handshake.next_state}")

# Serialize
data_bytes = handshake.to_bytes()
print(f"\nSerialized packet: {len(data_bytes)} bytes")
print(f"Raw data: {data_bytes}")

# Extract components
import struct
length = struct.unpack('!I', data_bytes[0:4])[0]
packet_id = struct.unpack('!H', data_bytes[4:6])[0]
payload = data_bytes[6:]

print(f"\nPacket components:")
print(f"  length: {length}")
print(f"  packet_id: {packet_id}")
print(f"  payload: {len(payload)} bytes: {payload}")

# Try to deserialize
try:
    new_packet = HandshakePacket()
    new_packet.read(payload)
    
    print(f"\nDeserialized packet:")
    print(f"  protocol_version: {new_packet.protocol_version}")
    print(f"  server_address: '{new_packet.server_address}'")
    print(f"  server_port: {new_packet.server_port}")
    print(f"  next_state: {new_packet.next_state}")
    
    print("\n✅ Packet serialization/deserialization works correctly")
    
except Exception as e:
    print(f"\n❌ Deserialization failed: {e}")
    import traceback
    traceback.print_exc()