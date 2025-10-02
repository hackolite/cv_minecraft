# Quick Start Guide - HTTP API

## Starting the Server

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python3 server.py
```

The server will start:
- **WebSocket Server** on `ws://localhost:8765` (for game clients)
- **HTTP API Server** on `http://localhost:8000` (for REST API)

## Quick Test

Open your browser to:
- **API Home:** http://localhost:8000/
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Basic Usage

### Get Cameras
```bash
curl http://localhost:8000/api/cameras
```

### Get Users
```bash
curl http://localhost:8000/api/users
```

### Get Blocks
```bash
curl "http://localhost:8000/api/blocks?min_x=60&max_x=70&min_y=95&max_y=105&min_z=60&max_z=70"
```

### Render View
```bash
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d '{"position": [64, 100, 64], "rotation": [0, 0]}' \
  -o view.png
```

## Python Usage

```python
import requests

# Get cameras
cameras = requests.get('http://localhost:8000/api/cameras').json()
print(f"Found {cameras['count']} cameras")

# Get users
users = requests.get('http://localhost:8000/api/users').json()
print(f"Found {users['count']} users")

# Render a view
img = requests.post('http://localhost:8000/api/render', json={
    'position': [64, 100, 64],
    'rotation': [0, 0],
    'width': 800,
    'height': 600
})
with open('view.png', 'wb') as f:
    f.write(img.content)
```

## Running Tests

### Basic Tests
```bash
python3 test_api_endpoints.py
```

### Integration Tests
```bash
python3 test_api_integration.py
```

### Example Usage
```bash
python3 example_api_usage.py
```

## Documentation

- **Full API Reference:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Implementation Details:** [HTTP_API_SUMMARY.md](HTTP_API_SUMMARY.md)
- **Interactive Docs:** http://localhost:8000/docs (when server is running)

## Troubleshooting

### Server Not Starting
- Check if port 8000 or 8765 is already in use
- Install missing dependencies: `pip install -r requirements.txt`

### Connection Refused
- Make sure the server is running: `python3 server.py`
- Check firewall settings if accessing remotely

### No Cameras Found
- Cameras are created during world initialization
- Check server logs for world initialization messages

## Next Steps

1. Explore the interactive Swagger UI at http://localhost:8000/docs
2. Run the example scripts in `example_api_usage.py`
3. Read the full API documentation in `API_DOCUMENTATION.md`
4. Build your own integrations using the API endpoints
