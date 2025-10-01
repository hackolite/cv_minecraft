# Cube Abstraction System

## Overview

This implementation creates an abstraction where each user connection to the Minecraft server creates a Cube object that can host child cubes. Each cube represents a player or entity in the game world.

## Architecture

### Components

1. **Cube Class** (`protocol.py`)
   - Base cube with position, rotation, and size
   - Child cube creation and management
   - Movement and camera control

2. **CubeManager** (`cube_manager.py`)
   - Central port allocation and management
   - Port range: 8081-8999 (avoiding reserved ports 8080, 8765)
   - Thread-safe port allocation and release
   - Port availability checking

3. **MinecraftServer** (`server.py`)
   - Automatic cube creation on user connection
   - Cube cleanup on user disconnection
   - Integration with existing WebSocket protocol

## User Connection Flow

```
1. User connects via WebSocket to ws://localhost:8765
2. Server creates PlayerState for the user
3. Server creates Cube object for the user
4. User can control cube via game controls
5. User can create child cubes programmatically
6. On disconnect, all cubes are cleaned up
```

## Usage Examples

### Starting the Server
```bash
python demo_cube_server.py
```

### Connecting and Testing
1. Connect WebSocket client to `ws://localhost:8765`
2. Send player join message
3. Control your cube via game interface

## Features

✅ **Thread-Safe Management**: Cube management is thread-safe  
✅ **Child Cube Support**: Parent cubes can create and manage child cubes  
✅ **Movement System**: Complete movement with proper trigonometry  
✅ **Camera Control**: Camera rotation support  
✅ **Automatic Cleanup**: Cubes automatically cleaned up on disconnect  
✅ **Real-time Updates**: Cube positions update in real-time  

## Testing

Run the comprehensive test suite:

```bash
# Test core cube system
python test_cube_system.py

# Test server integration
python test_server_integration.py
```

## Configuration

### Port Range
Modify in `cube_manager.py`:
```python
cube_manager = CubeManager(port_start=8081, port_end=8999)
```

### Reserved Ports
- 8765: Main Minecraft WebSocket server  
- 8081+: Available for future use

## Implementation Details

### Movement Calculations
Movement uses proper trigonometry based on cube rotation:
- Forward/Back: Uses sin/cos of horizontal rotation
- Left/Right: Uses perpendicular angles for strafing
- Jump: Simple Y-axis translation

### Port Management
- Checks port availability using socket connections
- Thread-safe allocation with locks
- Automatic cleanup on cube destruction
- Avoids system and reserved ports

### Server Integration  
- Cubes created in `register_client()` 
- Cubes destroyed in `unregister_client()`
- No interference with existing WebSocket protocol
- Maintains compatibility with existing client code

## Future Enhancements

- [ ] Integrate with actual camera system for image capture
- [ ] Add cube-to-cube communication
- [ ] Implement physics sync between cube movement and game world
- [ ] Add cube collision detection
- [ ] Support for different cube types and capabilities
- [ ] Persistent cube state across reconnections
- [ ] Add more sophisticated movement controls