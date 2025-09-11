"""
Game client with separated concerns
Handles game logic separately from networking and rendering
"""

import asyncio
import time
import threading
import logging
from typing import Optional, List, Dict, Tuple
from .network_client import NetworkClient
from .renderer import Renderer


logger = logging.getLogger(__name__)


class GameClient:
    """
    Main game client with pyCraft-inspired architecture
    Separates networking, game logic, and rendering
    """
    
    def __init__(self, username: str = "Player", render_enabled: bool = True):
        self.username = username
        self.render_enabled = render_enabled
        
        # Components
        self.network_client = NetworkClient(username)
        self.renderer: Optional[Renderer] = None
        
        # Game state
        self.world_blocks: Dict[Tuple[int, int, int], str] = {}
        self.players: Dict[str, dict] = {}
        self.inventory = ["BRICK", "GRASS", "SAND", "WOOD", "LEAF"]
        self.selected_block = "BRICK"
        
        # Input state
        self.input_state = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False,
            'jump': False,
            'crouch': False,
            'sprint': False,
            'flying': False
        }
        
        # Player state
        self.position = [30.0, 50.0, 80.0]
        self.rotation = [0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.on_ground = True
        
        # Game loop
        self.running = False
        self.tick_rate = 20  # 20 TPS
        self._game_loop_task: Optional[asyncio.Task] = None
        self._last_position_update = 0
        
        # Setup network callbacks
        self._setup_network_callbacks()
    
    def _setup_network_callbacks(self):
        """Setup network event callbacks"""
        self.network_client.on_login_success = self._on_login_success
        self.network_client.on_world_update = self._on_world_update
        self.network_client.on_block_change = self._on_block_change
        self.network_client.on_chat_message = self._on_chat_message
        self.network_client.on_disconnect = self._on_disconnect
    
    async def start(self, host: str = "localhost", port: int = 8766):
        """Start the game client"""
        logger.info(f"Starting game client for {self.username}")
        
        # Initialize renderer if enabled
        if self.render_enabled:
            self.renderer = Renderer()
            await self._setup_renderer()
        
        # Connect to server
        connected = await self.network_client.connect(host, port)
        if not connected:
            logger.error("Failed to connect to server")
            return False
        
        # Start game loop
        self.running = True
        self._game_loop_task = asyncio.create_task(self._game_loop())
        
        # Start renderer if enabled
        if self.renderer:
            await self.renderer.start()
        
        return True
    
    async def _setup_renderer(self):
        """Setup renderer callbacks"""
        if not self.renderer:
            return
        
        # Register input callbacks
        self.renderer.on_key_press = self._on_key_press
        self.renderer.on_key_release = self._on_key_release
        self.renderer.on_mouse_press = self._on_mouse_press
        self.renderer.on_mouse_motion = self._on_mouse_motion
        
        # Register world callbacks
        self.renderer.set_world_data(self.world_blocks)
    
    async def _game_loop(self):
        """Main game loop"""
        last_tick = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_tick
            last_tick = current_time
            
            # Update game logic
            await self._update_game_logic(dt)
            
            # Send position updates periodically
            if current_time - self._last_position_update > 0.05:  # 20 updates per second
                await self._send_position_update()
                self._last_position_update = current_time
            
            # Sleep until next tick
            sleep_time = max(0, (1.0 / self.tick_rate) - (time.time() - current_time))
            await asyncio.sleep(sleep_time)
    
    async def _update_game_logic(self, dt: float):
        """Update game logic"""
        # Update player movement
        self._update_movement(dt)
        
        # Update renderer if enabled
        if self.renderer:
            self.renderer.update_player_position(self.position, self.rotation)
    
    def _update_movement(self, dt: float):
        """Update player movement based on input"""
        # Movement constants
        speed = 15.0 if self.input_state['flying'] else 5.0
        if self.input_state['sprint'] and not self.input_state['flying']:
            speed = 7.0
        elif self.input_state['crouch']:
            speed = 2.0
        
        # Calculate movement vector
        movement = [0.0, 0.0, 0.0]
        
        # Forward/backward
        if self.input_state['forward']:
            movement[2] -= 1.0
        if self.input_state['backward']:
            movement[2] += 1.0
        
        # Left/right
        if self.input_state['left']:
            movement[0] -= 1.0
        if self.input_state['right']:
            movement[0] += 1.0
        
        # Apply rotation to movement
        if movement[0] != 0 or movement[2] != 0:
            import math
            yaw = math.radians(self.rotation[0])
            cos_yaw = math.cos(yaw)
            sin_yaw = math.sin(yaw)
            
            dx = movement[0] * cos_yaw - movement[2] * sin_yaw
            dz = movement[0] * sin_yaw + movement[2] * cos_yaw
            
            # Normalize
            length = math.sqrt(dx * dx + dz * dz)
            if length > 0:
                dx /= length
                dz /= length
            
            # Apply speed and delta time
            self.position[0] += dx * speed * dt
            self.position[2] += dz * speed * dt
        
        # Vertical movement
        if self.input_state['flying']:
            if self.input_state['jump']:
                self.position[1] += speed * dt
            if self.input_state['crouch']:
                self.position[1] -= speed * dt
        else:
            # Gravity and jumping
            if self.input_state['jump'] and self.on_ground:
                self.velocity[1] = 8.0  # Jump velocity
                self.on_ground = False
            
            # Apply gravity
            if not self.on_ground:
                self.velocity[1] -= 20.0 * dt  # Gravity
                self.position[1] += self.velocity[1] * dt
                
                # Simple ground collision
                if self.position[1] <= 1.0:
                    self.position[1] = 1.0
                    self.velocity[1] = 0.0
                    self.on_ground = True
    
    async def _send_position_update(self):
        """Send position update to server"""
        if self.network_client.is_connected():
            await self.network_client.send_position_update(
                self.position[0], self.position[1], self.position[2],
                self.rotation[0], self.rotation[1], self.on_ground
            )
    
    # Network event handlers
    
    async def _on_login_success(self, username: str, uuid: str, spawn_pos: List[float]):
        """Handle successful login"""
        logger.info(f"Logged in as {username}")
        self.position = spawn_pos
    
    async def _on_world_update(self, blocks: List[dict]):
        """Handle world update from server"""
        logger.info(f"Received world update with {len(blocks)} blocks")
        
        # Update world blocks
        for block_data in blocks:
            pos = tuple(block_data["pos"])
            block_type = block_data["type"]
            self.world_blocks[pos] = block_type
        
        # Update renderer
        if self.renderer:
            self.renderer.update_world_blocks(self.world_blocks)
    
    async def _on_block_change(self, x: int, y: int, z: int, block_type: str, action: str):
        """Handle block change from server"""
        pos = (x, y, z)
        
        if action == "place":
            self.world_blocks[pos] = block_type
        elif action == "remove":
            self.world_blocks.pop(pos, None)
        
        # Update renderer
        if self.renderer:
            self.renderer.update_single_block(pos, block_type if action == "place" else None)
    
    async def _on_chat_message(self, sender: str, message: str, timestamp: float):
        """Handle chat message"""
        logger.info(f"[{sender}]: {message}")
        
        # Update renderer chat if available
        if self.renderer:
            self.renderer.add_chat_message(sender, message)
    
    async def _on_disconnect(self, reason: str):
        """Handle disconnect"""
        logger.info(f"Disconnected from server: {reason}")
        await self.stop()
    
    # Input handlers
    
    def _on_key_press(self, key: str):
        """Handle key press"""
        if key == 'w':
            self.input_state['forward'] = True
        elif key == 's':
            self.input_state['backward'] = True
        elif key == 'a':
            self.input_state['left'] = True
        elif key == 'd':
            self.input_state['right'] = True
        elif key == 'space':
            self.input_state['jump'] = True
        elif key == 'lshift':
            self.input_state['crouch'] = True
        elif key == 'lctrl':
            self.input_state['sprint'] = True
        elif key == 'tab':
            self.input_state['flying'] = not self.input_state['flying']
        elif key in ['1', '2', '3', '4', '5']:
            index = int(key) - 1
            if 0 <= index < len(self.inventory):
                self.selected_block = self.inventory[index]
    
    def _on_key_release(self, key: str):
        """Handle key release"""
        if key == 'w':
            self.input_state['forward'] = False
        elif key == 's':
            self.input_state['backward'] = False
        elif key == 'a':
            self.input_state['left'] = False
        elif key == 'd':
            self.input_state['right'] = False
        elif key == 'space':
            self.input_state['jump'] = False
        elif key == 'lshift':
            self.input_state['crouch'] = False
        elif key == 'lctrl':
            self.input_state['sprint'] = False
    
    async def _on_mouse_press(self, button: str, x: float, y: float):
        """Handle mouse press"""
        if not self.network_client.is_connected():
            return
        
        # Calculate target block position (simplified)
        # In a real implementation, this would use raycasting
        target_pos = [
            int(self.position[0] + 5),
            int(self.position[1]),
            int(self.position[2] + 5)
        ]
        
        if button == 'left':
            # Remove block
            await self.network_client.send_block_change(
                target_pos[0], target_pos[1], target_pos[2], "", "remove"
            )
        elif button == 'right':
            # Place block
            await self.network_client.send_block_change(
                target_pos[0], target_pos[1], target_pos[2], 
                self.selected_block, "place"
            )
    
    def _on_mouse_motion(self, dx: float, dy: float):
        """Handle mouse motion"""
        sensitivity = 0.15
        self.rotation[0] += dx * sensitivity
        self.rotation[1] += dy * sensitivity
        
        # Clamp vertical rotation
        self.rotation[1] = max(-90, min(90, self.rotation[1]))
    
    async def send_chat(self, message: str):
        """Send chat message"""
        if self.network_client.is_connected():
            await self.network_client.send_chat_message(message)
    
    async def stop(self):
        """Stop the game client"""
        logger.info("Stopping game client")
        
        self.running = False
        
        # Stop game loop
        if self._game_loop_task:
            self._game_loop_task.cancel()
        
        # Stop renderer
        if self.renderer:
            await self.renderer.stop()
        
        # Disconnect from server
        await self.network_client.disconnect("Client shutting down")
    
    def get_stats(self) -> dict:
        """Get client statistics"""
        stats = {
            'username': self.username,
            'position': self.position,
            'rotation': self.rotation,
            'world_blocks': len(self.world_blocks),
            'running': self.running,
            'render_enabled': self.render_enabled
        }
        
        # Add network stats
        network_stats = self.network_client.get_stats()
        stats.update({'network_' + k: v for k, v in network_stats.items()})
        
        return stats