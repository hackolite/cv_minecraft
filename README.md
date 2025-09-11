# Minecraft - Multiplayer Client-Server Architecture

This is a Minecraft-like game implemented with a true client-server architecture supporting multiplayer gameplay through an agent-based system. The server manages all world logic, player actions, and state synchronization while clients act as visual agents connecting via WebSocket.

## 🚨 Important: Display Requirements

**If you're experiencing invisible blocks, this is likely due to missing display requirements.**

### For Headless/Server Environments
```shell
# Install virtual display
sudo apt-get install xvfb

# Run with virtual display
xvfb-run -a python3 client/client.py
xvfb-run -a python3 minecraft.py
```

### For SSH Connections
```shell
# Connect with X11 forwarding
ssh -X username@hostname

# Then run normally
python3 client/client.py
```

### For Local Systems
Ensure you have a running display server (X11 or Wayland) before starting the game.

## Architecture

### Agent-Based Multiplayer System
- **Server (`/server/server.py`)**: Handles WebSocket clients, maintains world state, manages player agents, broadcasts updates
- **Client (`/client/client.py`)**: Handles local game loop with Pyglet, connects via WebSocket, visualizes world, sends player actions to server
- **True Client-Server**: All game logic (block placement, player movement, inventory, etc.) is strictly server-side
- **Agent Representation**: Each connected client is represented as a distinct agent on the server with its own state (position, inventory, etc.)
- **Regular Updates**: Server broadcasts updates at a regular tick rate to all clients

### Communication Protocol

**Client-to-Server Messages:**
```json
// Join the game
{"type": "join", "name": "PlayerName"}

// Move player
{"type": "move", "pos": [12, 50, 21], "rotation": [0, 0]}

// Place/remove blocks
{"type": "block", "pos": [12, 49, 21], "action": "place", "block_type": "STONE"}
{"type": "block", "pos": [12, 49, 21], "action": "remove"}

// Chat message
{"type": "chat", "message": "Hello world!"}
```

**Server-to-Client Messages:**
```json
// World state update
{
  "type": "world_update",
  "blocks": [{"pos": [10, 49, 20], "type": "GRASS"}, ...],
  "player": {"name": "Alice", "pos": [10, 50, 20], "rotation": [0, 0]}
}

// Player updates
{
  "type": "update", 
  "players": [{"name": "Alice", "pos": [10, 50, 20]}, ...],
  "timestamp": 1234567890
}
```

## How to Run

### Prerequisites
```shell
pip install -r requirements.txt

# For headless environments (servers without display)
sudo apt-get install xvfb
```

### Starting the Server
```shell
python3 server/server.py
```
The server will:
- Generate a procedural world with terrain, water, and trees
- Start listening on `ws://localhost:8765`
- Handle multiple client connections
- Manage all game logic server-side

### Starting a Client
```shell
# For systems with display
python3 client/client.py

# For headless systems (recommended for servers)
xvfb-run -a python3 client/client.py

# For SSH connections
ssh -X username@hostname
python3 client/client.py
```
Each client will:
- Connect to the server as an agent
- Display the 3D world using Pyglet
- Send player actions to the server
- Receive and display world updates

### Controls (Client)
- **WASD**: Move (ZQSD on French keyboards)  
- **Mouse**: Look around
- **Space**: Jump
- **Left Click**: Remove block
- **Right Click**: Place block
- **1-5**: Select block type
- **Tab**: Toggle flying mode
- **Escape**: Release mouse cursor

## Features

### Server Features
- **Procedural World Generation**: Terrain with hills, water, sand beaches, and trees
- **Multi-Client Support**: Handle multiple simultaneous players
- **Block Management**: Server-side validation of block placement/removal
- **Player State**: Position, inventory, flying mode for each agent
- **Real-time Updates**: Regular broadcasts of world state changes
- **Collision Detection**: Server validates movement and prevents clipping

### Client Features
- **3D Rendering**: Pyglet-based OpenGL rendering with textures
- **Network Synchronization**: Real-time world state updates from server
- **Input Handling**: WASD movement, mouse look, block interaction
- **Visual Feedback**: Crosshair, player position display, block count
- **Agent Behavior**: Acts as autonomous agent sending actions to server

### Block Types
- **GRASS**: Green surface blocks with dirt sides
- **STONE**: Gray underground material  
- **SAND**: Beach and desert material
- **WOOD**: Tree trunks
- **LEAF**: Tree foliage
- **WATER**: Fluid blocks in low areas
- **BRICK**: Player-buildable construction material

## Extensibility

The agent-based architecture supports easy extension with:

### AI Agents
```python
# Add bot players that can connect and act autonomously
class AIAgent:
    async def connect_to_server(self):
        # Connect as WebSocket client
        # Implement AI behavior (pathfinding, building, etc.)
```

### Custom Block Types
```python
# Server-side block type registration
CUSTOM_BLOCK = "CUSTOM"
# Client-side texture mapping
BLOCK_TEXTURES["CUSTOM"] = custom_texture_coords
```

### Game Modes
- Creative mode with unlimited resources
- Survival mode with health and hunger
- PvP combat between player agents
- Collaborative building projects

## Technical Details

- **Language**: Python 3.12+
- **Graphics**: Pyglet with OpenGL
- **Networking**: WebSockets for real-time communication
- **Architecture**: True client-server with agent-based players
- **World Format**: Block-based 3D voxel world
- **Terrain**: Procedural generation using noise algorithms

## Troubleshooting

### Problem: "None of the blocks are visible" / "aucun des blocs n'est visible"

**Root Cause:** The game requires a display server (X11/Wayland) to render blocks. Without it, Pyglet cannot initialize the graphics system.

**Solutions:**

1. **For headless servers:**
   ```shell
   sudo apt-get install xvfb
   xvfb-run -a python3 client/client.py
   ```

2. **For SSH connections:**
   ```shell
   ssh -X username@hostname
   python3 client/client.py
   ```

3. **For local systems:**
   - Ensure X11 or Wayland is running
   - Check DISPLAY environment variable: `echo $DISPLAY`

### Problem: "Library GLU not found"
```shell
sudo apt-get install libglu1-mesa-dev
```

### Problem: WebSocket connection failed
```shell
# Make sure server is running first
python3 server/server.py

# Then start client
python3 client/client.py
```

## Development

### Running Tests
```shell
python3 test_connection.py
```

### Architecture Benefits
1. **Scalable Multiplayer**: Server handles all authoritative game state
2. **Cheat Prevention**: Clients cannot modify world without server validation  
3. **Consistent State**: All players see the same synchronized world
4. **Agent Extensibility**: Easy to add AI bots or specialized client types
5. **Network Efficiency**: Only necessary updates are broadcast to clients

Original base game by [Fogleman](https://github.com/fogleman/Minecraft), extended for multiplayer agent-based architecture.
