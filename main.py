#!/usr/bin/env python3
"""
Minecraft Client-Server Launcher

This file provides compatibility with the old single-file approach.
For the new client-server architecture, run:
  - python3 server.py (to start the server)
  - python3 client.py (to start the client)
"""

import sys

print("=" * 60)
print("MINECRAFT CLIENT-SERVER")
print("=" * 60)
print()
print("This game has been converted to client-server architecture.")
print()
print("To play:")
print("1. Start the server:  python3 server.py")
print("2. Start the client:  python3 client.py")
print()
print("Multiple clients can connect to the same server!")
print()
print("For the original monolithic version, run: python3 minecraft.py")
print()
print("=" * 60)

# Only import the old minecraft if explicitly requested
if len(sys.argv) > 1 and sys.argv[1] == "--old":
    print("Starting original monolithic version...")
    import minecraft