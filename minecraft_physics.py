#!/usr/bin/env python3
"""
Standard Minecraft Physics System
================================

This module implements standard Minecraft-style physics for collision detection,
gravity, and block positioning. It follows the canonical Minecraft specifications
for player dimensions, collision boxes, and physics constants.

Key Features:
- Precise block collision detection with proper bounding boxes
- Standard Minecraft player dimensions (0.6×1.8×0.6 blocks)
- Proper gravity and terminal velocity
- Accurate ground detection and block snapping
- Compatible with both client and server implementations
"""

import math
from typing import Tuple, List, Dict, Optional, Set

# Standard Minecraft Physics Constants
PLAYER_WIDTH = 0.6          # Player width (X and Z dimensions)
PLAYER_HEIGHT = 1.8         # Player height (Y dimension)
PLAYER_EYE_HEIGHT = 1.62    # Eye height from feet

# Physics constants matching Minecraft's behavior
GRAVITY = 32.0              # Blocks per second squared (stronger than current)
TERMINAL_VELOCITY = 78.4    # Maximum falling speed
JUMP_VELOCITY = 10.0        # Initial jump speed
WALKING_SPEED = 4.317       # Blocks per second
SPRINTING_SPEED = 5.612     # Blocks per second  
FLYING_SPEED = 10.89        # Blocks per second

# Collision constants
COLLISION_EPSILON = 0.001   # Small value for floating point precision
STEP_HEIGHT = 0.5625        # Maximum step up height (9/16 blocks)

# World constants
BLOCK_SIZE = 1.0            # Each block is 1×1×1

def normalize_position(position: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """
    Normalize a position to block coordinates.
    Standard Minecraft floors negative coordinates differently.
    """
    x, y, z = position
    return int(math.floor(x)), int(math.floor(y)), int(math.floor(z))


def get_player_bounding_box(position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Get the player's bounding box given their position.
    
    Args:
        position: Player position (x, y, z) where y is at feet level
        
    Returns:
        Tuple of (min_corner, max_corner) representing the bounding box
    """
    x, y, z = position
    half_width = PLAYER_WIDTH / 2
    
    min_corner = (x - half_width, y, z - half_width)
    max_corner = (x + half_width, y + PLAYER_HEIGHT, z + half_width)
    
    return min_corner, max_corner


def get_blocks_in_bounding_box(min_corner: Tuple[float, float, float], 
                              max_corner: Tuple[float, float, float]) -> Set[Tuple[int, int, int]]:
    """
    Get all block coordinates that intersect with the given bounding box.
    
    Args:
        min_corner: Minimum corner of bounding box
        max_corner: Maximum corner of bounding box
        
    Returns:
        Set of block coordinates that intersect the bounding box
    """
    x_min, y_min, z_min = min_corner
    x_max, y_max, z_max = max_corner
    
    # Get integer bounds for blocks
    block_x_min = int(math.floor(x_min))
    block_x_max = int(math.floor(x_max))
    block_y_min = int(math.floor(y_min))
    block_y_max = int(math.floor(y_max))
    block_z_min = int(math.floor(z_min))
    block_z_max = int(math.floor(z_max))
    
    blocks = set()
    for x in range(block_x_min, block_x_max + 1):
        for y in range(block_y_min, block_y_max + 1):
            for z in range(block_z_min, block_z_max + 1):
                blocks.add((x, y, z))
    
    return blocks


def box_intersects_block(min_corner: Tuple[float, float, float], 
                        max_corner: Tuple[float, float, float],
                        block_pos: Tuple[int, int, int]) -> bool:
    """
    Check if a bounding box intersects with a specific block.
    
    Args:
        min_corner: Minimum corner of bounding box
        max_corner: Maximum corner of bounding box  
        block_pos: Block position (integer coordinates)
        
    Returns:
        True if the bounding box intersects the block
    """
    box_x_min, box_y_min, box_z_min = min_corner
    box_x_max, box_y_max, box_z_max = max_corner
    
    block_x, block_y, block_z = block_pos
    block_x_min, block_y_min, block_z_min = float(block_x), float(block_y), float(block_z)
    block_x_max, block_y_max, block_z_max = float(block_x + 1), float(block_y + 1), float(block_z + 1)
    
    # Check for intersection in all three dimensions with small epsilon for floating point precision
    # Use > instead of >= to avoid edge case issues
    x_intersect = box_x_min < block_x_max - COLLISION_EPSILON and box_x_max > block_x_min + COLLISION_EPSILON
    y_intersect = box_y_min < block_y_max - COLLISION_EPSILON and box_y_max > block_y_min + COLLISION_EPSILON
    z_intersect = box_z_min < block_z_max - COLLISION_EPSILON and box_z_max > block_z_min + COLLISION_EPSILON
    
    return x_intersect and y_intersect and z_intersect


class MinecraftCollisionDetector:
    """
    Standard Minecraft collision detection system.
    
    This class implements the collision detection logic used in Minecraft,
    with proper handling of player bounding boxes, block collision, and
    physics calculations.
    """
    
    def __init__(self, world_blocks: Dict[Tuple[int, int, int], str]):
        """
        Initialize the collision detector.
        
        Args:
            world_blocks: Dictionary mapping block positions to block types
        """
        self.world_blocks = world_blocks
        
    def check_collision(self, position: Tuple[float, float, float]) -> bool:
        """
        Check if the player would collide with any blocks at the given position.
        
        Args:
            position: Player position to test
            
        Returns:
            True if collision would occur, False otherwise
        """
        min_corner, max_corner = get_player_bounding_box(position)
        potential_blocks = get_blocks_in_bounding_box(min_corner, max_corner)
        
        for block_pos in potential_blocks:
            if block_pos in self.world_blocks:
                if box_intersects_block(min_corner, max_corner, block_pos):
                    return True
        
        return False
    
    def find_ground_level(self, x: float, z: float, start_y: float = 256.0) -> Optional[float]:
        """
        Find the ground level at the given X, Z coordinates.
        
        Args:
            x: X coordinate
            z: Z coordinate
            start_y: Y coordinate to start searching from (searches downward)
            
        Returns:
            Y coordinate of the ground surface, or None if no ground found
        """
        # Search downward from start_y to find the highest solid block
        for y in range(int(start_y), -64, -1):  # Search down to bedrock level
            block_pos = (int(math.floor(x)), y, int(math.floor(z)))
            if block_pos in self.world_blocks:
                return float(y + 1)  # Return top surface of the block
        
        return None
    
    def resolve_collision(self, old_position: Tuple[float, float, float], 
                         new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Resolve collision between old and new position, returning a safe position.
        
        This implements standard Minecraft collision resolution, testing movement
        on each axis separately to allow sliding along walls.
        
        Args:
            old_position: Previous player position
            new_position: Desired new position
            
        Returns:
            Tuple of (safe_position, collision_info) where collision_info indicates
            which directions had collisions: {'x': bool, 'y': bool, 'z': bool, 'ground': bool}
        """
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        current_x, current_y, current_z = old_x, old_y, old_z
        
        # Test Y movement first (gravity/jumping)
        test_y_pos = (current_x, new_y, current_z)
        if not self.check_collision(test_y_pos):
            current_y = new_y
        else:
            collision_info['y'] = True
            # If moving down and hitting something, we're on ground
            if new_y < old_y:
                collision_info['ground'] = True
                # Snap to the surface of the block we hit
                ground_level = self.find_ground_level(current_x, current_z, old_y)
                if ground_level is not None:
                    current_y = ground_level
        
        # Test X movement
        test_x_pos = (new_x, current_y, current_z)
        if not self.check_collision(test_x_pos):
            current_x = new_x
        else:
            collision_info['x'] = True
        
        # Test Z movement  
        test_z_pos = (current_x, current_y, new_z)
        if not self.check_collision(test_z_pos):
            current_z = new_z
        else:
            collision_info['z'] = True
        
        # Final ground check - see if we're supported by ground
        ground_test_pos = (current_x, current_y - COLLISION_EPSILON, current_z)
        if self.check_collision(ground_test_pos):
            collision_info['ground'] = True
        
        return (current_x, current_y, current_z), collision_info
    
    def snap_to_ground(self, position: Tuple[float, float, float], 
                      max_step_down: float = 1.0) -> Tuple[float, float, float]:
        """
        Snap the player to the ground if they're close to it.
        
        This helps with consistent ground detection and prevents floating
        slightly above blocks due to floating point precision.
        
        Args:
            position: Current player position
            max_step_down: Maximum distance to search for ground below
            
        Returns:
            Adjusted position snapped to ground
        """
        x, y, z = position
        
        # Search for ground below current position
        for test_y in [y - i * 0.0625 for i in range(int(max_step_down * 16))]:  # Test in 1/16 block increments
            test_pos = (x, test_y, z)
            if not self.check_collision(test_pos):
                continue
                
            # Found ground, place player just above it
            ground_level = self.find_ground_level(x, z, test_y + 1.0)
            if ground_level is not None:
                return (x, ground_level, z)
        
        return position


class MinecraftPhysics:
    """
    Standard Minecraft physics system.
    
    Handles gravity, terminal velocity, jumping, and movement physics
    according to Minecraft specifications.
    """
    
    def __init__(self, collision_detector: MinecraftCollisionDetector):
        """
        Initialize the physics system.
        
        Args:
            collision_detector: Collision detection system to use
        """
        self.collision_detector = collision_detector
    
    def apply_gravity(self, velocity_y: float, dt: float, on_ground: bool) -> float:
        """
        Apply gravity to vertical velocity.
        
        Args:
            velocity_y: Current vertical velocity
            dt: Time delta in seconds
            on_ground: Whether the player is on ground
            
        Returns:
            New vertical velocity after gravity
        """
        if on_ground and velocity_y <= 0:
            return 0.0  # No falling if on ground
        
        # Apply gravity acceleration
        new_velocity = velocity_y - GRAVITY * dt
        
        # Apply terminal velocity limit
        return max(new_velocity, -TERMINAL_VELOCITY)
    
    def update_position(self, position: Tuple[float, float, float],
                       velocity: Tuple[float, float, float],
                       dt: float,
                       on_ground: bool,
                       jumping: bool) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], bool]:
        """
        Update player position and velocity with physics.
        
        Args:
            position: Current position
            velocity: Current velocity (vx, vy, vz)
            dt: Time delta in seconds
            on_ground: Whether player is currently on ground
            jumping: Whether player is attempting to jump
            
        Returns:
            Tuple of (new_position, new_velocity, new_on_ground)
        """
        x, y, z = position
        vx, vy, vz = velocity
        
        # Handle jumping
        if jumping and on_ground:
            vy = JUMP_VELOCITY
            on_ground = False
        
        # Apply gravity
        vy = self.apply_gravity(vy, dt, on_ground)
        
        # Calculate new position
        new_x = x + vx * dt
        new_y = y + vy * dt
        new_z = z + vz * dt
        
        # Resolve collisions
        new_position, collision_info = self.collision_detector.resolve_collision(
            (x, y, z), (new_x, new_y, new_z)
        )
        
        # Update velocity based on collisions
        final_vx, final_vy, final_vz = vx, vy, vz
        
        if collision_info['x']:
            final_vx = 0.0
        if collision_info['y']:
            final_vy = 0.0
        if collision_info['z']:
            final_vz = 0.0
        
        # Update ground status
        new_on_ground = collision_info['ground']
        
        # If we're falling and hit ground, snap to proper position
        if new_on_ground and not on_ground:
            new_position = self.collision_detector.snap_to_ground(new_position)
        
        return new_position, (final_vx, final_vy, final_vz), new_on_ground


# Compatibility functions for existing code
def minecraft_collide(position: Tuple[float, float, float], 
                     height: int,
                     world_blocks: Dict[Tuple[int, int, int], str]) -> Tuple[float, float, float]:
    """
    Compatibility function for existing collision detection code.
    
    Args:
        position: Player position to test
        height: Player height in blocks (ignored, uses standard height)
        world_blocks: World block dictionary
        
    Returns:
        Safe position after collision resolution
    """
    detector = MinecraftCollisionDetector(world_blocks)
    physics = MinecraftPhysics(detector)
    
    # For compatibility, we'll do a simple collision check and return safe position
    safe_position, _ = detector.resolve_collision(position, position)
    return safe_position


def minecraft_check_ground(position: Tuple[float, float, float],
                          world_blocks: Dict[Tuple[int, int, int], str]) -> bool:
    """
    Compatibility function to check if player is on ground.
    
    Args:
        position: Player position
        world_blocks: World block dictionary
        
    Returns:
        True if player is on ground
    """
    detector = MinecraftCollisionDetector(world_blocks)
    x, y, z = position
    
    # Check slightly below current position
    test_position = (x, y - COLLISION_EPSILON, z)
    return detector.check_collision(test_position)