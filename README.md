# Minecraft Client-Server

This is a Minecraft-like game converted to client-server architecture using Panda3D for rendering and WebSocket for communication.

Original project based on Fogleman's "Minecraft" which was created for an April Fools video.

https://github.com/fogleman/Minecraft

Video here: https://www.youtube.com/watch?v=S4EUQD9QIzc&lc=z23mubkgxpapjvhot04t1aokgeofqomvondp5x4qnz1abk0h00410

## Architecture

The game is now split into two components:

- **Server** (`server.py`): Manages the game world, handles multiplayer connections via WebSocket
- **Client** (`client.py`): Renders the game using Panda3D, handles user input and networking

## How to Run

### Installation

```shell
pip install -r requirements.txt
```

### Starting the Game

1. **Start the Server** (in one terminal):
```shell
python3 server.py
```

2. **Start the Client** (in another terminal):
```shell
python3 client.py
```

Multiple clients can connect to the same server for multiplayer functionality.

## Controls

### Movement Controls (Both QWERTY and AZERTY keyboard layouts supported)
- **WASD** or **ZQSD**: Movement (forward/backward/left/right) 
- **Space/C**: Move up/down
- **Arrow Keys**: Look around (keyboard fallback)
- **Mouse**: Look around (smooth camera rotation)
- **Left Click**: Remove block
- **Right Click**: Place block
- **1-6**: Select block type (Brick, Grass, Sand, Wood, Leaf, Frog)
- **Tab**: Toggle flying mode
- **R**: Request world data (debug client)
- **T**: Test block placement (debug client)

### Improved Controls
- **Configurable mouse sensitivity**: Smooth and responsive camera rotation
- **Dual keyboard layout support**: Works with both QWERTY and AZERTY layouts
- **Responsive movement**: Improved keyboard control responsiveness

## Features

- **Multiplayer Support**: Multiple players can connect simultaneously
- **Real-time Synchronization**: Block changes are synchronized across all clients
- **Procedural World Generation**: Large 128x128 world with terrain, trees, and water
- **Physics**: Gravity, jumping, collision detection
- **Block Types**: 6 different block types with distinct textures
- **Flying Mode**: Toggle between walking and flying
- **Improved Rendering**: Configurable block sizes and consistent visual quality
- **Enhanced Controls**: Smooth mouse controls and responsive keyboard input

## Technical Details

- **Server**: Python WebSocket server managing world state (256K+ blocks)
- **Client**: Panda3D-based 3D renderer with physics and networking
- **Protocol**: JSON-based WebSocket messages for real-time communication
- **World Format**: Blocks stored as position-texture pairs
- **Rendering**: Simple colored cubes (can be extended with full textures)
- **Data Transfer**: Chunked loading for large worlds (>500 blocks sent in chunks)
- **3D Engine**: Proper depth testing and perspective rendering enabled

## Testing

Run the test suite:

```shell
python3 test_connection.py      # Test basic connectivity
python3 verify_fix.py          # Verify block rendering fix
python3 test_3d_rendering.py   # Test 3D rendering capabilities
```

This will test:
- Client imports and dependencies
- Server terrain generation  
- Network connectivity (requires server to be running)
- Chunked world data transfer
- 3D block rendering and positioning
