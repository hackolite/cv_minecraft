"""
Shared protocol definitions for client-server communication.
Defines message types and data structures used between client and server.
"""

import json
import asyncio
import socket
import threading
import time
import io
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Set
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

# Pyglet and OpenGL imports for window abstraction
try:
    import pyglet
    from pyglet.gl import *
    from PIL import Image
    PYGLET_AVAILABLE = True
    print("✅ Pyglet and OpenGL are available for window abstraction")
except ImportError as e:
    PYGLET_AVAILABLE = False
    print(f"⚠️  Pyglet/OpenGL not available: {e}. Using dummy classes.")
    # Create dummy classes for headless compatibility
    class DummyWindow:
        def __init__(self, **kwargs):
            self.width = kwargs.get('width', 800)
            self.height = kwargs.get('height', 600)
            self.visible = kwargs.get('visible', False)
        def close(self):
            pass
        def get_size(self):
            return (self.width, self.height)
        def dispatch_event(self, event):
            pass
        def switch_to(self):
            pass

class MessageType(Enum):
    """Types of messages exchanged between client and server."""
    # Client to Server
    PLAYER_JOIN = "player_join"
    PLAYER_MOVE = "player_move"
    PLAYER_LOOK = "player_look"
    BLOCK_PLACE = "block_place"
    BLOCK_DESTROY = "block_destroy"
    CHAT_MESSAGE = "chat_message"
    PLAYER_DISCONNECT = "player_disconnect"

    # Server to Client
    WORLD_INIT = "world_init"
    WORLD_CHUNK = "world_chunk"
    WORLD_UPDATE = "world_update"
    PLAYER_UPDATE = "player_update"
    BLOCK_UPDATE = "block_update"
    CHAT_BROADCAST = "chat_broadcast"
    PLAYER_LIST = "player_list"
    ERROR = "error"

class BlockType:
    """Block type definitions shared between client and server."""
    GRASS = "grass"
    SAND = "sand"
    BRICK = "brick"
    STONE = "stone"
    WOOD = "wood"
    LEAF = "leaf"
    WATER = "water"
    CAMERA = "camera"  # Camera block visible to all users
    AIR = "air"  # Represents removed blocks

class Message:
    """Base message class for client-server communication."""

    def __init__(self, msg_type: MessageType, data: Dict[str, Any], player_id: Optional[str] = None):
        self.type = msg_type
        self.data = data
        self.player_id = player_id
        self.timestamp = None  # Can be added for timing

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "player_id": self.player_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string."""
        data = json.loads(json_str)
        msg_type = MessageType(data["type"])
        return cls(msg_type, data["data"], data.get("player_id"))


class CubeWindow:
    """Pyglet window abstraction for camera-type cubes."""
    
    def __init__(self, cube_id: str, width: int = 800, height: int = 600, visible: bool = False):
        """Initialize a cube window."""
        self.cube_id = cube_id
        self.width = width
        self.height = height
        self.visible = visible
        self.window = None
        self.app_running = False
        
        if PYGLET_AVAILABLE:
            try:
                # Create an offscreen window for rendering (not visible by default)
                self.window = pyglet.window.Window(
                    width=width, 
                    height=height, 
                    visible=visible,
                    caption=f'Cube {cube_id} View'
                )
                
                # Basic OpenGL setup
                self._setup_opengl()
                
                print(f"✅ Created pyglet window for cube {cube_id}")
                
            except Exception as e:
                print(f"⚠️  Failed to create pyglet window for cube {cube_id}: {e}")
                self.window = DummyWindow(width=width, height=height, visible=visible)
        else:
            print(f"⚠️  Pyglet not available, using dummy window for cube {cube_id}")
            self.window = DummyWindow(width=width, height=height, visible=visible)
    
    def _setup_opengl(self):
        """Basic OpenGL setup for the cube window."""
        if not PYGLET_AVAILABLE or not self.window:
            return
            
        try:
            # Make this window's context current
            self.window.switch_to()
            
            # Basic OpenGL setup
            glEnable(GL_DEPTH_TEST)
            glClearColor(0.5, 0.7, 1.0, 1.0)  # Sky blue background
            
        except Exception as e:
            print(f"⚠️  OpenGL setup failed for cube {self.cube_id}: {e}")
    
    def take_screenshot(self) -> Optional[bytes]:
        """Take a screenshot of the cube's view."""
        if not PYGLET_AVAILABLE or not self.window or not hasattr(self.window, 'get_size'):
            return None
            
        try:
            # Make sure this window's context is current
            self.window.switch_to()
            
            # Clear and render a simple scene
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Simple cube rendering (placeholder - in real implementation this would render the world from cube's perspective)
            self._render_simple_scene()
            
            # Force flush to ensure rendering is complete
            glFlush()
            
            # Read pixels from framebuffer
            width, height = self.window.get_size()
            pixels = (GLubyte * (3 * width * height))(0)
            glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, pixels)
            
            # Convert to PIL Image and flip vertically
            image = Image.frombytes('RGB', (width, height), pixels)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            
            # Convert to PNG bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"⚠️  Screenshot failed for cube {self.cube_id}: {e}")
            return None
    
    def _render_simple_scene(self):
        """Render a simple scene from the cube's perspective."""
        if not PYGLET_AVAILABLE:
            return
            
        try:
            # Set up 3D perspective
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            
            # Set perspective projection
            width, height = self.window.get_size()
            aspect = width / float(height) if height > 0 else 1.0
            
            # Simple perspective setup
            glFrustum(-aspect, aspect, -1, 1, 1, 100)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            # Move camera back
            glTranslatef(0, 0, -5)
            
            # Draw a simple colored cube as placeholder
            self._draw_colored_cube()
            
        except Exception as e:
            print(f"⚠️  Scene rendering failed for cube {self.cube_id}: {e}")
    
    def _draw_colored_cube(self):
        """Draw a simple colored cube."""
        if not PYGLET_AVAILABLE:
            return
            
        try:
            # Define cube vertices
            vertices = [
                # Front face
                -1, -1,  1,   1, -1,  1,   1,  1,  1,  -1,  1,  1,
                # Back face
                -1, -1, -1,  -1,  1, -1,   1,  1, -1,   1, -1, -1,
                # Top face
                -1,  1, -1,  -1,  1,  1,   1,  1,  1,   1,  1, -1,
                # Bottom face
                -1, -1, -1,   1, -1, -1,   1, -1,  1,  -1, -1,  1,
                # Right face
                 1, -1, -1,   1,  1, -1,   1,  1,  1,   1, -1,  1,
                # Left face
                -1, -1, -1,  -1, -1,  1,  -1,  1,  1,  -1,  1, -1,
            ]
            
            # Define colors for each face
            colors = [
                1.0, 0.0, 0.0,  1.0, 0.0, 0.0,  1.0, 0.0, 0.0,  1.0, 0.0, 0.0,  # Red front
                0.0, 1.0, 0.0,  0.0, 1.0, 0.0,  0.0, 1.0, 0.0,  0.0, 1.0, 0.0,  # Green back
                0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  # Blue top
                1.0, 1.0, 0.0,  1.0, 1.0, 0.0,  1.0, 1.0, 0.0,  1.0, 1.0, 0.0,  # Yellow bottom
                1.0, 0.0, 1.0,  1.0, 0.0, 1.0,  1.0, 0.0, 1.0,  1.0, 0.0, 1.0,  # Magenta right
                0.0, 1.0, 1.0,  0.0, 1.0, 1.0,  0.0, 1.0, 1.0,  0.0, 1.0, 1.0,  # Cyan left
            ]
            
            # Draw the cube using quads
            glBegin(GL_QUADS)
            for i in range(24):  # 6 faces * 4 vertices
                glColor3f(colors[i*3], colors[i*3+1], colors[i*3+2])
                glVertex3f(vertices[i*3], vertices[i*3+1], vertices[i*3+2])
            glEnd()
            
        except Exception as e:
            print(f"⚠️  Cube drawing failed for cube {self.cube_id}: {e}")
    
    def close(self):
        """Close the cube window and clean up resources."""
        if self.window and hasattr(self.window, 'close'):
            try:
                self.window.close()
                print(f"✅ Closed window for cube {self.cube_id}")
            except Exception as e:
                print(f"⚠️  Error closing window for cube {self.cube_id}: {e}")
        self.window = None


class Cube:
    """Base class representing a cube in the game world with FastAPI server capabilities."""
    
    def __init__(self, cube_id: str, position: Tuple[float, float, float],
                 rotation: Tuple[float, float] = (0, 0), size: float = 0.5, 
                 base_url: str = "localhost", auto_start_server: bool = False,
                 cube_type: str = "normal"):
        self.id = cube_id
        self.position = position  # (x, y, z)
        self.rotation = rotation  # (horizontal, vertical)
        self.size = size  # Half-size of the cube (cube extends from -size to +size)
        self.velocity = [0.0, 0.0, 0.0]  # (dx, dy, dz)
        self.color = None  # Will be set by the model
        self.cube_type = cube_type  # Type of cube: "normal", "camera", etc.
        
        # Server-related attributes
        self.base_url = base_url
        self.port = None  # Will be assigned dynamically
        self.app = None  # FastAPI application
        self.server_thread = None
        self.running = False
        
        # Child cube management
        self.child_cubes: Dict[str, 'Cube'] = {}
        self.parent_cube: Optional['Cube'] = None
        
        # Camera and status
        self.status = "active"
        
        # Window abstraction for certain cube types (especially camera types)
        self.window = None  # Will be created for camera-type cubes
        
        # Create window for camera-type cubes
        if self.cube_type == "camera":
            self._create_window()
        
        if auto_start_server:
            self.setup_fastapi_server()
    
    def update_position(self, position: Tuple[float, float, float]):
        """Update the cube's position with validation."""
        if not isinstance(position, (tuple, list)) or len(position) != 3:
            raise ValueError(f"Position must be a 3-element tuple/list, got: {position}")
        
        x, y, z = position
        if not all(isinstance(coord, (int, float)) for coord in [x, y, z]):
            raise ValueError(f"Position coordinates must be numeric: {position}")
        
        self.position = position
    
    def update_rotation(self, rotation: Tuple[float, float]):
        """Update the cube's rotation."""
        self.rotation = rotation
    
    def get_render_position(self) -> Tuple[float, float, float]:
        """Get the position for rendering (positioned on ground with bottom touching surface)."""
        x, y, z = self.position
        
        # Defensive validation: ensure position is valid
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not isinstance(z, (int, float)):
            raise ValueError(f"Invalid position values: {self.position}")
        
        # Calculate render position: cube center is elevated by size so bottom touches surface at Y
        render_y = y + self.size
        return (x, render_y, z)  # Elevate by half-size so bottom touches ground

    def _create_window(self):
        """Create a pyglet window for this cube (used for camera-type cubes)."""
        try:
            self.window = CubeWindow(self.id, width=800, height=600, visible=False)
            print(f"✅ Created window for {self.cube_type} cube {self.id}")
        except Exception as e:
            print(f"⚠️  Failed to create window for cube {self.id}: {e}")
            self.window = None

    def setup_fastapi_server(self):
        """Setup FastAPI server for this cube."""
        if self.app is not None:
            return  # Already setup
            
        self.app = FastAPI(title=f"Cube {self.id} API", version="1.0.0")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes for cube control."""
        
        @self.app.get("/")
        async def get_info():
            """Get cube information."""
            return {
                "cube_id": self.id,
                "position": self.position,
                "rotation": self.rotation,
                "status": self.status,
                "color": self.color,
                "cube_type": self.cube_type,
                "has_window": self.window is not None,
                "base_url": f"http://{self.base_url}:{self.port}",
                "child_cubes": list(self.child_cubes.keys())
            }
        
        @self.app.get("/status")
        async def get_status():
            """Get cube status and color."""
            return {
                "status": self.status,
                "color": self.color,
                "position": self.position,
                "running": self.running
            }
        
        @self.app.post("/move/forward")
        async def move_forward(distance: float = 1.0):
            """Move cube forward."""
            x, y, z = self.position
            # Calculate forward direction based on rotation
            h_rot = self.rotation[0]
            import math
            dx = -distance * math.sin(math.radians(h_rot))
            dz = -distance * math.cos(math.radians(h_rot))
            new_position = (x + dx, y, z + dz)
            self.update_position(new_position)
            return {"message": "Moved forward", "position": self.position}
        
        @self.app.post("/move/back")
        async def move_back(distance: float = 1.0):
            """Move cube backward."""
            x, y, z = self.position
            # Calculate backward direction based on rotation
            h_rot = self.rotation[0]
            import math
            dx = distance * math.sin(math.radians(h_rot))
            dz = distance * math.cos(math.radians(h_rot))
            new_position = (x + dx, y, z + dz)
            self.update_position(new_position)
            return {"message": "Moved back", "position": self.position}
        
        @self.app.post("/move/left")
        async def move_left(distance: float = 1.0):
            """Move cube left."""
            x, y, z = self.position
            # Calculate left direction based on rotation
            h_rot = self.rotation[0]
            import math
            dx = -distance * math.cos(math.radians(h_rot))
            dz = distance * math.sin(math.radians(h_rot))
            new_position = (x + dx, y, z + dz)
            self.update_position(new_position)
            return {"message": "Moved left", "position": self.position}
        
        @self.app.post("/move/right")
        async def move_right(distance: float = 1.0):
            """Move cube right."""
            x, y, z = self.position
            # Calculate right direction based on rotation
            h_rot = self.rotation[0]
            import math
            dx = distance * math.cos(math.radians(h_rot))
            dz = -distance * math.sin(math.radians(h_rot))
            new_position = (x + dx, y, z + dz)
            self.update_position(new_position)
            return {"message": "Moved right", "position": self.position}
        
        @self.app.post("/move/jump")
        async def jump(height: float = 2.0):
            """Make cube jump."""
            x, y, z = self.position
            new_position = (x, y + height, z)
            self.update_position(new_position)
            return {"message": f"Jumped {height} units", "position": self.position}
        
        @self.app.post("/camera/rotate")
        async def rotate_camera(horizontal: float = 0.0, vertical: float = 0.0):
            """Rotate cube's camera."""
            h, v = self.rotation
            new_rotation = (h + horizontal, v + vertical)
            self.update_rotation(new_rotation)
            return {"message": "Camera rotated", "rotation": self.rotation}
        
        @self.app.get("/camera/image")
        async def get_camera_image():
            """Get camera image from cube's window."""
            if not self.window:
                if self.cube_type == "camera":
                    return {"error": "Camera window not available", "message": "Window failed to initialize"}
                else:
                    return {"error": "Not a camera cube", "message": f"Cube type '{self.cube_type}' does not support camera images"}
            
            try:
                # Take screenshot from the cube's window
                screenshot_bytes = self.window.take_screenshot()
                if screenshot_bytes:
                    return StreamingResponse(
                        io.BytesIO(screenshot_bytes),
                        media_type="image/png"
                    )
                else:
                    return {"error": "Screenshot failed", "message": "Failed to capture image from cube window"}
            except Exception as e:
                return {"error": "Camera error", "message": f"Screenshot error: {str(e)}"}
        
        @self.app.post("/cubes/create")
        async def create_child_cube(child_id: str, x: float = 0.0, y: float = 0.0, z: float = 0.0, cube_type: str = "normal"):
            """Create a child cube."""
            try:
                child_cube = await self.create_child_cube(child_id, (x, y, z), cube_type)
                return {
                    "message": f"Child cube {child_id} created",
                    "child_cube": {
                        "id": child_cube.id,
                        "position": child_cube.position,
                        "port": child_cube.port,
                        "cube_type": child_cube.cube_type
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/cubes/{child_id}")
        async def destroy_child_cube(child_id: str):
            """Destroy a child cube."""
            try:
                await self.destroy_child_cube(child_id)
                return {"message": f"Child cube {child_id} destroyed"}
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @self.app.get("/cubes")
        async def list_child_cubes():
            """List all child cubes."""
            return {
                "child_cubes": [
                    {
                        "id": cube.id,
                        "position": cube.position,
                        "port": cube.port,
                        "status": cube.status
                    }
                    for cube in self.child_cubes.values()
                ]
            }

    async def create_child_cube(self, child_id: str, position: Tuple[float, float, float], cube_type: str = "normal") -> 'Cube':
        """Create a child cube with its own FastAPI server."""
        if child_id in self.child_cubes:
            raise ValueError(f"Child cube {child_id} already exists")
        
        # Create child cube with specified type
        child_cube = Cube(child_id, position, base_url=self.base_url, cube_type=cube_type)
        child_cube.parent_cube = self
        
        # Assign port from central manager
        from cube_manager import cube_manager
        child_cube.port = cube_manager.allocate_port()
        
        # Setup and start server
        child_cube.setup_fastapi_server()
        await child_cube.start_server()
        
        # Add to children
        self.child_cubes[child_id] = child_cube
        
        return child_cube
    
    async def destroy_child_cube(self, child_id: str):
        """Destroy a child cube and stop its server."""
        if child_id not in self.child_cubes:
            raise ValueError(f"Child cube {child_id} not found")
        
        child_cube = self.child_cubes[child_id]
        
        # Stop server and release port
        await child_cube.stop_server()
        from cube_manager import cube_manager
        cube_manager.release_port(child_cube.port)
        
        # Remove from children
        del self.child_cubes[child_id]
    
    async def start_server(self):
        """Start the FastAPI server for this cube."""
        if self.running or self.port is None:
            return
        
        if self.app is None:
            self.setup_fastapi_server()
        
        def run_server():
            try:
                uvicorn.run(self.app, host=self.base_url, port=self.port, log_level="warning")
            except Exception as e:
                print(f"Server error for cube {self.id}: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.running = True
        
        # Wait for server to start
        for _ in range(10):
            time.sleep(0.5)
            try:
                import requests
                response = requests.get(f"http://{self.base_url}:{self.port}/", timeout=1)
                if response.status_code == 200:
                    break
            except:
                continue
        
        print(f"🚀 Cube {self.id} server started on http://{self.base_url}:{self.port}")
    
    async def stop_server(self):
        """Stop the FastAPI server for this cube."""
        self.running = False
        
        # Stop all child cubes first
        for child_id in list(self.child_cubes.keys()):
            await self.destroy_child_cube(child_id)
        
        # Clean up window if it exists
        if self.window:
            self.window.close()
            self.window = None
        
        # Note: uvicorn doesn't have a clean stop method when run in thread
        # In production, we'd use a process-based approach
        if self.server_thread and self.server_thread.is_alive():
            print(f"🛑 Stopping server for cube {self.id}")
            # The thread will terminate when the main process exits

class PlayerState(Cube):
    """Represents a player's state in the game world. Extends Cube for unified handling."""

    def __init__(self, id: str, position: Tuple[float, float, float],
                 rotation: Tuple[float, float], name: Optional[str] = None, 
                 is_connected: bool = True, is_rtsp_user: bool = False):
        super().__init__(id, position, rotation, size=0.5)
        self.name = name or f"Player_{id[:8]}"
        self.flying = False
        self.sprinting = False
        self.on_ground = False
        self.is_local = False  # Flag to identify local player
        self.is_connected = is_connected  # Flag for connected WebSocket clients
        self.is_rtsp_user = is_rtsp_user  # Flag for RTSP users
        self.last_move_time = 0.0  # Timestamp of last voluntary movement

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "position": self.position,
            "rotation": self.rotation,
            "name": self.name,
            "flying": self.flying,
            "sprinting": self.sprinting,
            "velocity": self.velocity,
            "on_ground": self.on_ground,
            "size": self.size,
            "is_connected": self.is_connected,
            "is_rtsp_user": self.is_rtsp_user
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Create from dictionary."""
        player = cls(data["id"], tuple(data["position"]), tuple(data["rotation"]), 
                    data.get("name"), data.get("is_connected", True), data.get("is_rtsp_user", False))
        player.flying = data.get("flying", False)
        player.sprinting = data.get("sprinting", False)
        player.size = data.get("size", 0.5)
        return player

class BlockUpdate:
    """Represents a block change in the world."""

    def __init__(self, position: Tuple[int, int, int], block_type: str, player_id: Optional[str] = None):
        self.position = position
        self.block_type = block_type
        self.player_id = player_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "position": self.position,
            "block_type": self.block_type,
            "player_id": self.player_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockUpdate':
        """Create from dictionary."""
        return cls(tuple(data["position"]), data["block_type"], data.get("player_id"))

def create_player_join_message(player_name: str) -> Message:
    """Create a player join message."""
    return Message(MessageType.PLAYER_JOIN, {"name": player_name})

def create_player_move_message(position: Tuple[float, float, float],
                             rotation: Tuple[float, float]) -> Message:
    """Create a player movement message with absolute position updates."""
    return Message(MessageType.PLAYER_MOVE, {
        "position": position,
        "rotation": rotation
    })

def create_block_place_message(position: Tuple[int, int, int], block_type: str) -> Message:
    """Create a block placement message."""
    return Message(MessageType.BLOCK_PLACE, {
        "position": position,
        "block_type": block_type
    })

def create_block_destroy_message(position: Tuple[int, int, int]) -> Message:
    """Create a block destruction message."""
    return Message(MessageType.BLOCK_DESTROY, {
        "position": position
    })

def create_chat_message(text: str) -> Message:
    """Create a chat message."""
    return Message(MessageType.CHAT_MESSAGE, {"text": text})

def create_world_init_message(world_data: Dict[str, Any]) -> Message:
    """Create a world initialization message for new clients."""
    return Message(MessageType.WORLD_INIT, world_data)

def create_world_chunk_message(chunk_data: Dict[str, Any]) -> Message:
    """Create a world chunk message for streaming world data."""
    return Message(MessageType.WORLD_CHUNK, chunk_data)

def create_world_update_message(blocks: List[BlockUpdate]) -> Message:
    """Create a world update message with multiple block changes."""
    return Message(MessageType.WORLD_UPDATE, {
        "blocks": [block.to_dict() for block in blocks]
    })

def create_player_update_message(player: PlayerState) -> Message:
    """Create a player update message."""
    return Message(MessageType.PLAYER_UPDATE, player.to_dict())

def create_player_list_message(players: List[PlayerState]) -> Message:
    """Create a player list message."""
    import logging
    logger = logging.getLogger(__name__)
    
    player_dicts = []
    for player in players:
        player_dict = player.to_dict()
        player_dicts.append(player_dict)
        logger.info(f"Creating player list entry: {player.name} -> {player_dict}")
    
    logger.info(f"Player list message created with {len(player_dicts)} players")
    return Message(MessageType.PLAYER_LIST, {
        "players": player_dicts
    })
