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
import math
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Set

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
    GET_CAMERAS_LIST = "get_cameras_list"
    GET_USERS_LIST = "get_users_list"
    GET_BLOCKS_LIST = "get_blocks_list"

    # Server to Client
    WORLD_INIT = "world_init"
    WORLD_CHUNK = "world_chunk"
    WORLD_UPDATE = "world_update"
    PLAYER_UPDATE = "player_update"
    BLOCK_UPDATE = "block_update"
    CHAT_BROADCAST = "chat_broadcast"
    PLAYER_LIST = "player_list"
    CAMERAS_LIST = "cameras_list"
    USERS_LIST = "users_list"
    BLOCKS_LIST = "blocks_list"
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
    USER = "user"  # User/player block
    AIR = "air"  # Represents removed blocks
    CAT = "cat"  # Cat block

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
    
    def __init__(self, cube_id: str, width: int = 800, height: int = 600, visible: bool = False, model=None, cube=None):
        """Initialize a cube window.
        
        Args:
            cube_id: Unique identifier for this cube
            width: Window width in pixels
            height: Window height in pixels
            visible: Whether the window should be visible
            model: The world model to render (EnhancedClientModel instance)
            cube: The cube instance this window belongs to (for position/rotation)
        """
        self.cube_id = cube_id
        self.width = width
        self.height = height
        self.visible = visible
        self.window = None
        self.app_running = False
        self.model = model  # World model to render
        self.cube = cube  # Camera cube instance for position/rotation
        
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
        """Render the world from the cube's perspective."""
        if not PYGLET_AVAILABLE:
            return
            
        try:
            # If we have a model and cube, render the actual world from camera's perspective
            if self.model and self.cube:
                self._render_world_from_camera()
            else:
                # Fallback to simple colored cube if model/cube not available
                self._render_placeholder_cube()
            
        except Exception as e:
            print(f"⚠️  Scene rendering failed for cube {self.cube_id}: {e}")
    
    def _render_world_from_camera(self):
        """Render the actual world from the camera cube's perspective."""
        if not PYGLET_AVAILABLE or not self.model or not self.cube:
            return
        
        try:
            # Set up 3D perspective
            width, height = self.window.get_size()
            glEnable(GL_DEPTH_TEST)
            glViewport(0, 0, max(1, width), max(1, height))
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            
            # Use gluPerspective like the main window
            # FOV of 70 degrees, near plane at 0.1, far plane at 60.0
            from pyglet.gl import gluPerspective
            fov = 70.0
            aspect = width / float(height) if height > 0 else 1.0
            gluPerspective(fov, aspect, 0.1, 60.0)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            # Apply camera rotation from cube
            rotation_x, rotation_y = self.cube.rotation
            glRotatef(rotation_x, 0, 1, 0)
            glRotatef(-rotation_y, math.cos(math.radians(rotation_x)), 0, math.sin(math.radians(rotation_x)))
            
            # Apply camera position from cube
            camera_x, camera_y, camera_z = self.cube.position
            # Camera is elevated slightly (eye height)
            camera_y += 0.6
            glTranslatef(-camera_x, -camera_y, -camera_z)
            
            # Render the world using the model's batch
            glColor3d(1, 1, 1)
            if self.model.batch:
                self.model.batch.draw()
            
        except Exception as e:
            print(f"⚠️  World rendering failed for cube {self.cube_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def _render_placeholder_cube(self):
        """Render a simple colored cube as placeholder when model is not available."""
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
            print(f"⚠️  Placeholder rendering failed for cube {self.cube_id}: {e}")
    
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
    """Base class representing a cube in the game world."""
    
    def __init__(self, cube_id: str, position: Tuple[float, float, float],
                 rotation: Tuple[float, float] = (0, 0), size: float = 0.5, 
                 cube_type: str = "normal", owner: Optional[str] = None, model=None):
        self.id = cube_id
        self.position = position  # (x, y, z)
        self.rotation = rotation  # (horizontal, vertical)
        self.size = size  # Half-size of the cube (cube extends from -size to +size)
        self.velocity = [0.0, 0.0, 0.0]  # (dx, dy, dz)
        self.color = None  # Will be set by the model
        self.cube_type = cube_type  # Type of cube: "normal", "camera", etc.
        self.owner = owner  # Player ID who owns this cube (for camera cubes)
        
        # Child cube management
        self.child_cubes: Dict[str, 'Cube'] = {}
        self.parent_cube: Optional['Cube'] = None
        
        # Camera and status
        self.status = "active"
        
        # Window abstraction for certain cube types (especially camera types)
        self.window = None  # Will be created for camera-type cubes
        
        # Create window for camera-type cubes
        if self.cube_type == "camera":
            self._create_window(model=model)
    
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

    def _create_window(self, model=None):
        """Create a pyglet window for this cube (used for camera-type cubes).
        
        Args:
            model: Optional world model to render from camera's perspective
        """
        try:
            self.window = CubeWindow(self.id, width=800, height=600, visible=False, model=model, cube=self)
            print(f"✅ Created window for {self.cube_type} cube {self.id}")
        except Exception as e:
            print(f"⚠️  Failed to create window for cube {self.id}: {e}")
            self.window = None

    def create_child_cube(self, child_id: str, position: Tuple[float, float, float], cube_type: str = "normal", owner: Optional[str] = None) -> 'Cube':
        """Create a child cube."""
        if child_id in self.child_cubes:
            raise ValueError(f"Child cube {child_id} already exists")
        
        # Create child cube with specified type
        child_cube = Cube(child_id, position, cube_type=cube_type, owner=owner)
        child_cube.parent_cube = self
        
        # Add to children
        self.child_cubes[child_id] = child_cube
        
        return child_cube
    
    def destroy_child_cube(self, child_id: str):
        """Destroy a child cube."""
        if child_id not in self.child_cubes:
            raise ValueError(f"Child cube {child_id} not found")
        
        child_cube = self.child_cubes[child_id]
        
        # Clean up window if it exists
        if child_cube.window:
            child_cube.window.close()
            child_cube.window = None
        
        # Remove from children
        del self.child_cubes[child_id]

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

def create_cameras_list_message(cameras: List[Dict[str, Any]]) -> Message:
    """Create a cameras list message."""
    return Message(MessageType.CAMERAS_LIST, {
        "cameras": cameras
    })

def create_users_list_message(users: List[Dict[str, Any]]) -> Message:
    """Create a users list message."""
    return Message(MessageType.USERS_LIST, {
        "users": users
    })

def create_blocks_list_message(blocks: List[Dict[str, Any]]) -> Message:
    """Create a blocks list message."""
    return Message(MessageType.BLOCKS_LIST, {
        "blocks": blocks
    })
