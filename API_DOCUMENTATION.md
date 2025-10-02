# Server HTTP API Documentation

## Overview

The Minecraft server now provides a HTTP REST API in addition to the WebSocket interface. This API allows querying server state, retrieving camera positions, user information, and rendering views from specific positions.

## Base URL

```
http://localhost:8000
```

## API Endpoints

### 1. API Home

**Endpoint:** `GET /`

**Description:** Returns API information and available endpoints.

**Response:**
```json
{
  "name": "Minecraft Server API",
  "version": "1.0.0",
  "endpoints": {
    "cameras": "/api/cameras",
    "users": "/api/users",
    "blocks": "/api/blocks",
    "render": "/api/render"
  }
}
```

### 2. List Cameras

**Endpoint:** `GET /api/cameras`

**Description:** Returns a list of all camera blocks in the world.

**Response:**
```json
{
  "count": 5,
  "cameras": [
    {
      "position": [69, 102, 64],
      "block_type": "camera"
    },
    {
      "position": [59, 102, 64],
      "block_type": "camera"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/cameras
```

### 3. List Users

**Endpoint:** `GET /api/users`

**Description:** Returns a list of all connected users with their positions and state information.

**Response:**
```json
{
  "count": 2,
  "users": [
    {
      "id": "uuid-string",
      "name": "Player1",
      "position": [64.0, 100.0, 64.0],
      "rotation": [0.0, 0.0],
      "flying": false,
      "sprinting": false,
      "on_ground": true,
      "velocity": [0.0, 0.0, 0.0],
      "is_connected": true,
      "is_rtsp_user": false
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/users
```

### 4. Get Blocks in Area

**Endpoint:** `GET /api/blocks`

**Description:** Returns blocks in a specified 3D area.

**Query Parameters:**
- `min_x` (int, optional): Minimum X coordinate (default: 0)
- `min_y` (int, optional): Minimum Y coordinate (default: 0)
- `min_z` (int, optional): Minimum Z coordinate (default: 0)
- `max_x` (int, optional): Maximum X coordinate (default: WORLD_SIZE)
- `max_y` (int, optional): Maximum Y coordinate (default: 256)
- `max_z` (int, optional): Maximum Z coordinate (default: WORLD_SIZE)

**Response:**
```json
{
  "count": 150,
  "bounds": {
    "min": [60, 95, 60],
    "max": [70, 105, 70]
  },
  "blocks": [
    {
      "position": [64, 100, 64],
      "block_type": "grass"
    },
    {
      "position": [65, 100, 64],
      "block_type": "stone"
    }
  ]
}
```

**Example:**
```bash
# Get blocks in a 10x10x10 area around spawn
curl "http://localhost:8000/api/blocks?min_x=60&min_y=95&min_z=60&max_x=70&max_y=105&max_z=70"
```

### 5. Render View

**Endpoint:** `POST /api/render`

**Description:** Generates an image representing the view from a specific position and rotation. This endpoint can be used to reconstruct what a camera or user would see at any given position.

**Request Body (JSON):**
```json
{
  "position": [64.0, 100.0, 64.0],
  "rotation": [0.0, 0.0],
  "width": 640,
  "height": 480,
  "fov": 65.0,
  "render_distance": 50
}
```

**Parameters:**
- `position` (array of 3 floats, required): [x, y, z] coordinates of the camera
- `rotation` (array of 2 floats, required): [horizontal, vertical] angles in degrees
- `width` (int, optional): Image width in pixels (default: 640, max: 4096)
- `height` (int, optional): Image height in pixels (default: 480, max: 4096)
- `fov` (float, optional): Field of view in degrees (default: 65.0)
- `render_distance` (int, optional): Maximum distance to render blocks (default: 50)

**Response:** PNG image (binary data)

**Example:**
```bash
# Generate and save a view from spawn position
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d '{
    "position": [64.0, 100.0, 64.0],
    "rotation": [0.0, 0.0],
    "width": 800,
    "height": 600
  }' \
  -o view.png
```

**Python Example:**
```python
import requests

response = requests.post('http://localhost:8000/api/render', json={
    'position': [64.0, 100.0, 64.0],
    'rotation': [45.0, -30.0],
    'width': 1280,
    'height': 720,
    'render_distance': 50
})

if response.status_code == 200:
    with open('rendered_view.png', 'wb') as f:
        f.write(response.content)
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Use Cases

### 1. Monitoring Cameras

Get all camera positions and render views from each:

```python
import requests

# Get all cameras
cameras = requests.get('http://localhost:8000/api/cameras').json()

# Render view from each camera
for i, camera in enumerate(cameras['cameras']):
    response = requests.post('http://localhost:8000/api/render', json={
        'position': camera['position'],
        'rotation': [0.0, 0.0],
        'width': 640,
        'height': 480
    })
    with open(f'camera_{i}.png', 'wb') as f:
        f.write(response.content)
```

### 2. User Tracking

Monitor player positions and generate their current views:

```python
import requests
import time

while True:
    # Get all users
    users = requests.get('http://localhost:8000/api/users').json()
    
    for user in users['users']:
        print(f"User {user['name']} at {user['position']}")
        
        # Render their view
        response = requests.post('http://localhost:8000/api/render', json={
            'position': user['position'],
            'rotation': user['rotation']
        })
        
        with open(f"user_{user['name']}.png", 'wb') as f:
            f.write(response.content)
    
    time.sleep(5)
```

### 3. Area Analysis

Get all blocks in a specific area for analysis:

```python
import requests

# Get blocks around a specific location
response = requests.get('http://localhost:8000/api/blocks', params={
    'min_x': 50,
    'min_y': 90,
    'min_z': 50,
    'max_x': 80,
    'max_y': 110,
    'max_z': 80
})

blocks = response.json()
print(f"Found {blocks['count']} blocks")

# Count block types
from collections import Counter
block_types = Counter(b['block_type'] for b in blocks['blocks'])
print(block_types)
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `503 Service Unavailable`: Server not initialized

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Server Configuration

The HTTP API server runs on port 8000 by default. This can be configured by modifying the `start_http_api_server_thread()` call in `server.py`:

```python
# In main() function
start_http_api_server_thread(host='0.0.0.0', port=8000)
```

## Integration with WebSocket Server

The HTTP API runs in parallel with the WebSocket server (port 8765). Both servers share the same world state and player data:

- WebSocket server (port 8765): For real-time game communication
- HTTP API server (port 8000): For queries and rendering

This allows external tools to query the server state without interfering with game clients.

## Notes

- The render endpoint currently provides a simplified 2D projection. For full 3D rendering, integration with the pyglet rendering engine would be needed.
- Camera positions are automatically created during world initialization.
- The API is thread-safe and can handle multiple concurrent requests.
