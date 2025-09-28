# Cube Abstraction System with Dynamic Port Allocation

## Overview

This implementation creates an abstraction where each user connection to the Minecraft server creates a Cube object that can host child cubes with dynamic port allocation. Each cube runs its own FastAPI server providing complete movement and control capabilities.

## Architecture

### Components

1. **Enhanced Cube Class** (`protocol.py`)
   - Base cube with position, rotation, and size
   - Integrated FastAPI server with dedicated port
   - Child cube creation and management
   - Movement and camera control endpoints

2. **CubeManager** (`cube_manager.py`)
   - Central port allocation and management
   - Port range: 8081-8999 (avoiding reserved ports 8080, 8765)
   - Thread-safe port allocation and release
   - Port availability checking

3. **Enhanced MinecraftServer** (`server.py`)
   - Automatic cube creation on user connection
   - Cube cleanup on user disconnection
   - Integration with existing WebSocket protocol

## User Connection Flow

```
1. User connects via WebSocket to ws://localhost:8765
2. Server creates PlayerState for the user
3. Server creates Cube object for the user
4. CubeManager allocates dedicated port (e.g., 8081)
5. Cube starts FastAPI server on allocated port
6. User can control cube via HTTP API endpoints
7. User can create child cubes via parent cube API
8. On disconnect, all cubes and ports are cleaned up
```

## API Endpoints

Each cube provides the following REST API endpoints:

### Information
- `GET /` - Get cube information (ID, position, status, child cubes)
- `GET /status` - Get cube status and color

### Movement
- `POST /move/forward?distance=X` - Move forward by X units
- `POST /move/back?distance=X` - Move backward by X units  
- `POST /move/left?distance=X` - Move left by X units
- `POST /move/right?distance=X` - Move right by X units
- `POST /move/jump?height=X` - Jump by X units

### Camera Control
- `POST /camera/rotate?horizontal=X&vertical=Y` - Rotate camera
- `GET /camera/image` - Get camera image (placeholder)

### Child Cube Management
- `POST /cubes/create?child_id=ID&x=X&y=Y&z=Z` - Create child cube
- `DELETE /cubes/{child_id}` - Destroy child cube
- `GET /cubes` - List all child cubes

## Usage Examples

### Starting the Server
```bash
python demo_cube_server.py
```

### Connecting and Testing
1. Connect WebSocket client to `ws://localhost:8765`
2. Send player join message
3. Check server logs for allocated cube port
4. Use HTTP requests to control your cube

### Example API Calls
```bash
# Get cube information
curl http://localhost:8081/

# Move the cube
curl -X POST http://localhost:8081/move/forward?distance=5
curl -X POST http://localhost:8081/move/right?distance=3

# Jump
curl -X POST http://localhost:8081/move/jump?height=2

# Rotate camera
curl -X POST 'http://localhost:8081/camera/rotate?horizontal=45&vertical=10'

# Create child cube
curl -X POST 'http://localhost:8081/cubes/create?child_id=child1&x=10&y=50&z=10'

# List child cubes
curl http://localhost:8081/cubes

# Control child cube (on its own port)
curl http://localhost:8082/
curl -X POST http://localhost:8082/move/forward?distance=2
```

## Features

✅ **Dynamic Port Allocation**: Ports automatically allocated from 8081-8999 range  
✅ **Thread-Safe Management**: Port allocation and cube management is thread-safe  
✅ **Child Cube Support**: Parent cubes can create and manage child cubes  
✅ **Complete Movement API**: All basic movements with proper trigonometry  
✅ **Camera Control**: Camera rotation and image access endpoints  
✅ **Automatic Cleanup**: Cubes and ports automatically cleaned up on disconnect  
✅ **FastAPI Integration**: Each cube has OpenAPI documentation at `/docs`  
✅ **Real-time Updates**: Cube positions update in real-time via API calls  

## Testing

Run the comprehensive test suite:

```bash
# Test core cube system
python test_cube_system.py

# Test server integration
python test_server_integration.py

# Interactive API demo
python test_api_demo.py
```

## Configuration

### Port Range
Modify in `cube_manager.py`:
```python
cube_manager = CubeManager(port_start=8081, port_end=8999)
```

### Reserved Ports
- 8080: MinecraftClient FastAPI server
- 8765: Main Minecraft WebSocket server  
- 8081+: User cube FastAPI servers

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