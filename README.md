# Minecraft Client-Server (Pyglet-based)

This is a Minecraft-like game with client-server architecture using **Pyglet** for rendering and WebSocket for communication.

Original project based on Fogleman's "Minecraft" which was created for an April Fools video.

https://github.com/fogleman/Minecraft

Video here: https://www.youtube.com/watch?v=S4EUQD9QIzc&lc=z23mubkgxpapjvhot04t1aokgeofqomvondp5x4qnz1abk0h00410

## Architecture

The game is now split into two components:

- **Server** (`server.py`): Manages the game world, handles multiplayer connections via WebSocket
- **Pyglet Client** (`pyglet_client.py`): Renders the game using Pyglet, handles user input and networking

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

2. **Start the Pyglet Client** (in another terminal):
```shell
python3 pyglet_client.py
```

Multiple clients can connect to the same server for multiplayer functionality.

## Controls

### Movement Controls (Both QWERTY and AZERTY keyboard layouts supported)
- **WASD** or **ZQSD**: Movement (forward/backward/left/right) 
- **Space**: Jump
- **C**: Crouch / Zoom out
- **Arrow Keys**: Look around (keyboard fallback)
- **Mouse**: Look around (smooth camera rotation)
- **Left Click**: Remove block
- **Right Click**: Place block
- **1-6**: Select block type (Brick, Grass, Sand, Wood, Leaf, Frog)
- **Tab**: Toggle flying mode
- **R**: Sprint
- **Shift**: Crouch
- **F11**: Toggle fullscreen
- **ESC**: Release mouse capture

### Improved Controls
- **Configurable mouse sensitivity**: Smooth and responsive camera rotation
- **Dual keyboard layout support**: Works with both QWERTY and AZERTY layouts
- **Responsive movement**: Improved keyboard control responsiveness
- **Physics-based movement**: Gravity, jumping, and collision detection

## Features

- **Pyglet-based Rendering**: Uses Pyglet for efficient OpenGL rendering
- **Multiplayer Support**: Multiple players can connect simultaneously
- **Real-time Synchronization**: Block changes are synchronized across all clients
- **Procedural World Generation**: Terrain with hills, trees, and water
- **Physics**: Gravity, jumping, collision detection
- **Block Types**: 6 different block types with distinct textures
- **Flying Mode**: Toggle between walking and flying
- **Sprint and Crouch**: Enhanced movement mechanics
- **Mouse Controls**: Smooth camera rotation with mouse

## Technical Details

- **Server**: Python WebSocket server managing world state
- **Client**: Pyglet-based 3D renderer with physics and networking
- **Protocol**: JSON-based WebSocket messages for real-time communication
- **World Format**: Blocks stored as position-texture pairs
- **Rendering**: Textured cubes with efficient batched rendering
- **Data Transfer**: Chunked loading for large worlds (>500 blocks sent in chunks)
- **3D Engine**: OpenGL-based rendering with proper depth testing

## Testing

Run the test suite:

```shell
python3 test_pyglet_implementation.py  # Test pyglet implementation
python3 test_connection.py             # Test basic connectivity  
python3 verify_fix.py                  # Verify block rendering fix
```

This will test:
- Server world generation and management
- Pyglet client structure and game mechanics
- Network connectivity (requires server to be running)
- WebSocket communication protocol
- Block placement and removal system

## Alternative Clients

- **pyglet_client.py**: Pyglet-based client (main implementation)
- **client.py**: Panda3D-based client (legacy)
- **minecraft.py**: Original monolithic version
