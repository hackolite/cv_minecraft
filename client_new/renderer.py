"""
Renderer component for game client
Handles all rendering concerns separately from game logic and networking
"""

import asyncio
import logging
from typing import Dict, Tuple, Optional, Callable, List
import sys
import os

# Try to import Pyglet components
try:
    import pyglet
    from pyglet.gl import *
    from pyglet import image
    from pyglet.graphics import TextureGroup
    from pyglet.window import key, mouse
    
    # Try to import gluPerspective
    try:
        from pyglet.gl import gluPerspective
    except ImportError:
        try:
            from OpenGL.GL import gluPerspective
        except ImportError:
            print("Warning: gluPerspective not available")
    
    PYGLET_AVAILABLE = True
except ImportError as e:
    print(f"❌ Pyglet not available: {e}")
    PYGLET_AVAILABLE = False


logger = logging.getLogger(__name__)


class Renderer:
    """
    Renderer component with separated concerns
    Handles 3D rendering using Pyglet, independent of game logic
    """
    
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        
        # Rendering state
        self.window: Optional[object] = None
        self.batch: Optional[object] = None
        self.texture_group: Optional[object] = None
        
        # World data
        self.world_blocks: Dict[Tuple[int, int, int], str] = {}
        self.rendered_blocks: Dict[Tuple[int, int, int], object] = {}
        
        # Player state for rendering
        self.player_position = [0.0, 0.0, 0.0]
        self.player_rotation = [0.0, 0.0]
        
        # UI elements
        self.chat_messages: List[str] = []
        self.info_label: Optional[object] = None
        
        # Input callbacks
        self.on_key_press: Optional[Callable] = None
        self.on_key_release: Optional[Callable] = None
        self.on_mouse_press: Optional[Callable] = None
        self.on_mouse_motion: Optional[Callable] = None
        
        # Mouse state
        self.exclusive_mouse = False
        
        # Rendering queue
        self.render_queue = []
        
        # Check if rendering is available
        self.rendering_available = PYGLET_AVAILABLE
        
        if not self.rendering_available:
            logger.warning("Rendering not available - running in headless mode")
    
    async def start(self):
        """Start the renderer"""
        if not self.rendering_available:
            logger.info("Renderer disabled - no display available")
            return
        
        try:
            # Create window
            self.window = pyglet.window.Window(
                width=self.width, 
                height=self.height,
                caption='Minecraft-like Client (pyCraft-inspired)',
                resizable=True
            )
            
            # Setup OpenGL
            self._setup_opengl()
            
            # Create rendering batch
            self.batch = pyglet.graphics.Batch()
            
            # Load textures
            self._load_textures()
            
            # Setup window event handlers
            self._setup_window_events()
            
            # Create UI elements
            self._create_ui_elements()
            
            logger.info("Renderer started successfully")
            
            # Start rendering loop
            pyglet.app.run()
            
        except Exception as e:
            logger.error(f"Failed to start renderer: {e}")
            self.rendering_available = False
    
    def _setup_opengl(self):
        """Setup OpenGL state"""
        if not self.rendering_available:
            return
        
        glClearColor(0.5, 0.69, 1.0, 1)  # Sky blue background
        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        
        # Setup fog
        glEnable(GL_FOG)
        fog_color = (0.5, 0.69, 1.0, 1.0)
        glFogfv(GL_FOG_COLOR, (GLfloat * 4)(*fog_color))
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, 20.0)
        glFogf(GL_FOG_END, 60.0)
    
    def _load_textures(self):
        """Load game textures"""
        if not self.rendering_available:
            return
        
        # Try to load texture
        texture_path = 'texture.png'
        if not os.path.exists(texture_path):
            texture_path = '../texture.png'
        
        if os.path.exists(texture_path):
            try:
                texture = image.load(texture_path).get_texture()
                self.texture_group = TextureGroup(texture)
                logger.info(f"Loaded texture: {texture_path}")
            except Exception as e:
                logger.warning(f"Failed to load texture: {e}")
                self.texture_group = None
        else:
            logger.warning("Texture file not found")
            self.texture_group = None
    
    def _setup_window_events(self):
        """Setup window event handlers"""
        if not self.window:
            return
        
        @self.window.event
        def on_draw():
            self._on_draw()
        
        @self.window.event
        def on_resize(width, height):
            self._on_resize(width, height)
        
        @self.window.event
        def on_key_press(symbol, modifiers):
            self._on_key_press(symbol, modifiers)
        
        @self.window.event
        def on_key_release(symbol, modifiers):
            self._on_key_release(symbol, modifiers)
        
        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            self._on_mouse_press(x, y, button, modifiers)
        
        @self.window.event
        def on_mouse_motion(x, y, dx, dy):
            self._on_mouse_motion(x, y, dx, dy)
        
        @self.window.event
        def on_close():
            self._on_close()
    
    def _create_ui_elements(self):
        """Create UI elements"""
        if not self.window:
            return
        
        self.info_label = pyglet.text.Label(
            '', 
            font_name='Arial', 
            font_size=18,
            x=10, 
            y=self.window.height - 10, 
            anchor_x='left', 
            anchor_y='top',
            color=(255, 255, 255, 255)
        )
    
    def _on_draw(self):
        """Handle window drawing"""
        if not self.window:
            return
        
        self.window.clear()
        
        # Setup 3D rendering
        self._set_3d_projection()
        
        # Render world
        if self.batch:
            self.batch.draw()
        
        # Setup 2D rendering for UI
        self._set_2d_projection()
        
        # Draw UI elements
        self._draw_ui()
    
    def _set_3d_projection(self):
        """Setup 3D projection matrix"""
        if not self.window:
            return
        
        width, height = self.window.get_size()
        
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70.0, width / float(height), 0.1, 60.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Apply camera rotation and position
        x, y = self.player_rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        
        px, py, pz = self.player_position
        glTranslatef(-px, -py, -pz)
    
    def _set_2d_projection(self):
        """Setup 2D projection for UI"""
        if not self.window:
            return
        
        width, height = self.window.get_size()
        
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def _draw_ui(self):
        """Draw UI elements"""
        if not self.window:
            return
        
        # Draw crosshair
        self._draw_crosshair()
        
        # Draw info label
        if self.info_label:
            info_text = f"Pos: ({self.player_position[0]:.1f}, {self.player_position[1]:.1f}, {self.player_position[2]:.1f})"
            info_text += f" | Blocks: {len(self.world_blocks)}"
            self.info_label.text = info_text
            self.info_label.draw()
        
        # Draw chat messages
        self._draw_chat()
    
    def _draw_crosshair(self):
        """Draw crosshair in center of screen"""
        if not self.window:
            return
        
        width, height = self.window.get_size()
        cx, cy = width // 2, height // 2
        
        glColor3f(1, 1, 1)  # White
        glBegin(GL_LINES)
        glVertex2f(cx - 10, cy)
        glVertex2f(cx + 10, cy)
        glVertex2f(cx, cy - 10)
        glVertex2f(cx, cy + 10)
        glEnd()
    
    def _draw_chat(self):
        """Draw chat messages"""
        if not self.window or not self.chat_messages:
            return
        
        y_offset = 100
        for i, message in enumerate(self.chat_messages[-5:]):  # Show last 5 messages
            chat_label = pyglet.text.Label(
                message,
                font_name='Arial',
                font_size=14,
                x=10,
                y=y_offset + i * 20,
                anchor_x='left',
                anchor_y='bottom',
                color=(255, 255, 255, 200)
            )
            chat_label.draw()
    
    def _on_resize(self, width, height):
        """Handle window resize"""
        self.width = width
        self.height = height
        
        if self.info_label:
            self.info_label.y = height - 10
    
    def _on_key_press(self, symbol, modifiers):
        """Handle key press events"""
        key_name = self._symbol_to_key_name(symbol)
        
        # Handle escape key
        if symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        
        # Forward to game client
        if self.on_key_press:
            self.on_key_press(key_name)
    
    def _on_key_release(self, symbol, modifiers):
        """Handle key release events"""
        key_name = self._symbol_to_key_name(symbol)
        
        # Forward to game client
        if self.on_key_release:
            self.on_key_release(key_name)
    
    def _on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse press events"""
        if not self.exclusive_mouse:
            self.set_exclusive_mouse(True)
            return
        
        button_name = 'left' if button == mouse.LEFT else 'right' if button == mouse.RIGHT else 'middle'
        
        # Forward to game client
        if self.on_mouse_press:
            asyncio.create_task(self.on_mouse_press(button_name, x, y))
    
    def _on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse motion events"""
        if self.exclusive_mouse and self.on_mouse_motion:
            self.on_mouse_motion(dx, dy)
    
    def _on_close(self):
        """Handle window close"""
        logger.info("Renderer window closed")
        # Stop the Pyglet app
        pyglet.app.exit()
    
    def _symbol_to_key_name(self, symbol) -> str:
        """Convert Pyglet key symbol to string"""
        key_map = {
            key.W: 'w', key.A: 'a', key.S: 's', key.D: 'd',
            key.SPACE: 'space', key.LSHIFT: 'lshift', key.LCTRL: 'lctrl',
            key.TAB: 'tab', key.ESCAPE: 'escape',
            key._1: '1', key._2: '2', key._3: '3', key._4: '4', key._5: '5'
        }
        return key_map.get(symbol, str(symbol))
    
    def set_exclusive_mouse(self, exclusive: bool):
        """Set mouse capture mode"""
        if self.window:
            self.window.set_exclusive_mouse(exclusive)
            self.exclusive_mouse = exclusive
    
    def update_player_position(self, position: List[float], rotation: List[float]):
        """Update player position for rendering"""
        self.player_position = position[:]
        self.player_rotation = rotation[:]
    
    def set_world_data(self, world_blocks: Dict[Tuple[int, int, int], str]):
        """Set initial world data"""
        self.world_blocks = world_blocks
    
    def update_world_blocks(self, world_blocks: Dict[Tuple[int, int, int], str]):
        """Update all world blocks"""
        self.world_blocks.clear()
        self.world_blocks.update(world_blocks)
        
        # Clear existing rendered blocks
        for vertex_list in self.rendered_blocks.values():
            if hasattr(vertex_list, 'delete'):
                vertex_list.delete()
        self.rendered_blocks.clear()
        
        # Render new blocks
        self._render_all_blocks()
    
    def update_single_block(self, position: Tuple[int, int, int], block_type: Optional[str]):
        """Update a single block"""
        if block_type:
            self.world_blocks[position] = block_type
            self._render_block(position, block_type)
        else:
            self.world_blocks.pop(position, None)
            if position in self.rendered_blocks:
                vertex_list = self.rendered_blocks.pop(position)
                if hasattr(vertex_list, 'delete'):
                    vertex_list.delete()
    
    def _render_all_blocks(self):
        """Render all blocks in the world"""
        if not self.rendering_available or not self.batch:
            return
        
        for position, block_type in self.world_blocks.items():
            self._render_block(position, block_type)
    
    def _render_block(self, position: Tuple[int, int, int], block_type: str):
        """Render a single block"""
        if not self.rendering_available or not self.batch:
            return
        
        try:
            x, y, z = position
            
            # Get texture coordinates for block type
            texture_coords = self._get_texture_coords(block_type)
            
            # Create cube vertices
            vertices = self._create_cube_vertices(x, y, z, 0.5)
            
            # Create vertex list
            if self.texture_group:
                vertex_list = self.batch.add(24, GL_QUADS, self.texture_group,
                    ('v3f/static', vertices),
                    ('t2f/static', texture_coords))
            else:
                vertex_list = self.batch.add(24, GL_QUADS, None,
                    ('v3f/static', vertices))
            
            self.rendered_blocks[position] = vertex_list
            
        except Exception as e:
            logger.warning(f"Failed to render block at {position}: {e}")
    
    def _get_texture_coords(self, block_type: str) -> List[float]:
        """Get texture coordinates for a block type"""
        # Simplified texture mapping
        coords_map = {
            "GRASS": [0, 0, 1, 0, 1, 1, 0, 1] * 6,  # Repeat for all 6 faces
            "STONE": [2, 1, 3, 1, 3, 2, 2, 2] * 6,
            "SAND": [1, 1, 2, 1, 2, 2, 1, 2] * 6,
            "WOOD": [3, 1, 4, 1, 4, 2, 3, 2] * 6,
            "LEAF": [3, 0, 4, 0, 4, 1, 3, 1] * 6,
            "BRICK": [2, 0, 3, 0, 3, 1, 2, 1] * 6,
            "WATER": [0, 2, 1, 2, 1, 3, 0, 3] * 6
        }
        
        # Normalize coordinates (assuming 4x4 texture atlas)
        raw_coords = coords_map.get(block_type, [0, 0, 1, 0, 1, 1, 0, 1] * 6)
        return [coord / 4.0 for coord in raw_coords]
    
    def _create_cube_vertices(self, x: float, y: float, z: float, size: float) -> List[float]:
        """Create vertices for a cube"""
        return [
            # Top face
            x-size, y+size, z-size, x-size, y+size, z+size, x+size, y+size, z+size, x+size, y+size, z-size,
            # Bottom face
            x-size, y-size, z-size, x+size, y-size, z-size, x+size, y-size, z+size, x-size, y-size, z+size,
            # Left face
            x-size, y-size, z-size, x-size, y-size, z+size, x-size, y+size, z+size, x-size, y+size, z-size,
            # Right face
            x+size, y-size, z+size, x+size, y-size, z-size, x+size, y+size, z-size, x+size, y+size, z+size,
            # Front face
            x-size, y-size, z+size, x+size, y-size, z+size, x+size, y+size, z+size, x-size, y+size, z+size,
            # Back face
            x+size, y-size, z-size, x-size, y-size, z-size, x-size, y+size, z-size, x+size, y+size, z-size,
        ]
    
    def add_chat_message(self, sender: str, message: str):
        """Add a chat message to display"""
        chat_text = f"[{sender}]: {message}"
        self.chat_messages.append(chat_text)
        
        # Keep only last 10 messages
        if len(self.chat_messages) > 10:
            self.chat_messages.pop(0)
    
    async def stop(self):
        """Stop the renderer"""
        logger.info("Stopping renderer")
        
        if self.window:
            self.window.close()
        
        # Clean up rendered blocks
        for vertex_list in self.rendered_blocks.values():
            if hasattr(vertex_list, 'delete'):
                vertex_list.delete()
        self.rendered_blocks.clear()


# Import math for calculations
import math