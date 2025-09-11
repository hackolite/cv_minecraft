#!/usr/bin/env python3
"""
Launcher script for Minecraft-like multiplayer game
"""

import sys
import subprocess
import os

def main():
    if len(sys.argv) < 2:
        print("Minecraft-like Multiplayer Game")
        print("Usage: python3 launcher.py [server|client]")
        print("")
        print("Commands:")
        print("  server  - Start the game server")
        print("  client  - Start a game client")
        print("")
        print("Example:")
        print("  # Terminal 1 - Start server")
        print("  python3 launcher.py server")
        print("")
        print("  # Terminal 2 - Start client")
        print("  python3 launcher.py client")
        return

    command = sys.argv[1].lower()
    
    if command == "server":
        print("Starting Minecraft server...")
        subprocess.run([sys.executable, "server/server.py"])
    elif command == "client":
        print("Starting Minecraft client...")
        subprocess.run([sys.executable, "client/client.py"])
    else:
        print(f"Unknown command: {command}")
        print("Use 'server' or 'client'")

if __name__ == "__main__":
    main()