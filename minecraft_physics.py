#!/usr/bin/env python3
"""
Improved Minecraft Physics System
=================================

This module implements an improved Minecraft-style physics system with better
collision detection, more robust ground detection, and optimized performance.

Key Improvements:
- Better collision resolution order (X/Z first, then Y)
- Robust ground detection with clearance checking
- Optimized block testing with early exits
- Proper epsilon handling for floating point precision
- Cache system for repeated collision checks
"""

import math
from typing import Tuple, List, Dict, Optional, Set
from collections import defaultdict

# Standard Minecraft Physics Constants
PLAYER_WIDTH = 0.6          # Player width (X and Z dimensions)
PLAYER_HEIGHT = 1.8         # Player height (Y dimension)
PLAYER_EYE_HEIGHT = 1.62    # Eye height from feet

# Physics constants matching Minecraft's behavior
GRAVITY = 32.0              # Blocks per second squared
TERMINAL_VELOCITY = 78.4    # Maximum falling speed
JUMP_VELOCITY = 10.0        # Initial jump speed
WALKING_SPEED = 4.317       # Blocks per second
SPRINTING_SPEED = 5.612     # Blocks per second  
FLYING_SPEED = 10.89        # Blocks per second

# Collision constants
COLLISION_EPSILON = 0.001   # Small value for floating point precision
STEP_HEIGHT = 0.5625        # Maximum step up height (9/16 blocks)
GROUND_TOLERANCE = 0.05     # Distance to consider "on ground"

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
    
    # Get integer bounds for blocks - use proper rounding for edge cases
    block_x_min = int(math.floor(x_min + COLLISION_EPSILON))
    block_x_max = int(math.floor(x_max - COLLISION_EPSILON))
    block_y_min = int(math.floor(y_min + COLLISION_EPSILON))
    block_y_max = int(math.floor(y_max - COLLISION_EPSILON))
    block_z_min = int(math.floor(z_min + COLLISION_EPSILON))
    block_z_max = int(math.floor(z_max - COLLISION_EPSILON))
    
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
    Improved epsilon handling for consistent collision detection.
    
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
    block_x_min = float(block_x)
    block_y_min = float(block_y)
    block_z_min = float(block_z)
    block_x_max = float(block_x + 1)
    block_y_max = float(block_y + 1)
    block_z_max = float(block_z + 1)
    
    # Proper intersection test - boxes intersect if they overlap in ALL dimensions
    x_intersect = box_x_min < block_x_max and box_x_max > block_x_min
    y_intersect = box_y_min < block_y_max and box_y_max > block_y_min
    z_intersect = box_z_min < block_z_max and box_z_max > block_z_min
    
    return x_intersect and y_intersect and z_intersect


class MinecraftCollisionDetector:
    """
    Improved Minecraft collision detection system with caching and optimization.
    """
    
    def __init__(self, world_blocks: Dict[Tuple[int, int, int], str]):
        """
        Initialize the collision detector.
        
        Args:
            world_blocks: Dictionary mapping block positions to block types
        """
        self.world_blocks = world_blocks
        self.collision_cache = {}  # Cache recent collision checks
        self.cache_size = 1000  # Maximum cache entries
        
    def _cache_key(self, position: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Generate cache key for position (rounded to avoid float precision issues)"""
        x, y, z = position
        return (round(x * 1000), round(y * 1000), round(z * 1000))
    
    def check_collision(self, position: Tuple[float, float, float]) -> bool:
        """
        Check if the player would collide with any blocks at the given position.
        Now with caching for better performance.
        
        Args:
            position: Player position to test
            
        Returns:
            True if collision would occur, False otherwise
        """
        cache_key = self._cache_key(position)
        
        # Check cache first
        if cache_key in self.collision_cache:
            return self.collision_cache[cache_key]
        
        min_corner, max_corner = get_player_bounding_box(position)
        potential_blocks = get_blocks_in_bounding_box(min_corner, max_corner)
        
        collision = False
        for block_pos in potential_blocks:
            if block_pos in self.world_blocks:
                if box_intersects_block(min_corner, max_corner, block_pos):
                    collision = True
                    break  # Early exit on first collision
        
        # Update cache (with size limit)
        if len(self.collision_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.collision_cache))
            del self.collision_cache[oldest_key]
        
        self.collision_cache[cache_key] = collision
        return collision
    
    def find_ground_level(self, x: float, z: float, start_y: float = 256.0, 
                         check_clearance: bool = True) -> Optional[float]:
        """
        Find the ground level at the given X, Z coordinates with improved accuracy.
        
        Args:
            x: X coordinate
            z: Z coordinate
            start_y: Y coordinate to start searching from (searches downward)
            check_clearance: Whether to verify player has clearance above ground
            
        Returns:
            Y coordinate of the ground surface, or None if no ground found
        """
        # Search downward from start_y to find the highest solid block
        for y in range(int(start_y), -64, -1):
            block_pos = (int(math.floor(x)), y, int(math.floor(z)))
            if block_pos in self.world_blocks:
                ground_y = float(y + 1)  # Top surface of the block
                
                # Check if player has enough clearance above this ground level
                if check_clearance:
                    test_position = (x, ground_y, z)
                    if not self.check_collision(test_position):
                        return ground_y
                else:
                    return ground_y
        
        return None
    
    def resolve_collision(self, old_position: Tuple[float, float, float], 
                         new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Resolve collision with improved order: horizontal movement first, then vertical.
        This provides more natural movement behavior.
        
        Args:
            old_position: Previous player position
            new_position: Desired new position
            
        Returns:
            Tuple of (safe_position, collision_info)
        """
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        current_x, current_y, current_z = old_x, old_y, old_z
        
        # Test X movement first (horizontal)
        test_x_pos = (new_x, current_y, current_z)
        if not self.check_collision(test_x_pos):
            current_x = new_x
        else:
            collision_info['x'] = True
        
        # Test Z movement (horizontal)
        test_z_pos = (current_x, current_y, new_z)
        if not self.check_collision(test_z_pos):
            current_z = new_z
        else:
            collision_info['z'] = True
        
        # Test Y movement last (vertical)
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
        
        # Final ground check - more robust ground detection
        self._update_ground_status(collision_info, (current_x, current_y, current_z))
        
        return (current_x, current_y, current_z), collision_info
    
    def _update_ground_status(self, collision_info: Dict[str, bool], 
                            position: Tuple[float, float, float]) -> None:
        """Update ground status with more robust detection"""
        x, y, z = position
        
        # Check if we're close to ground by testing slightly below
        for test_distance in [COLLISION_EPSILON, GROUND_TOLERANCE]:
            ground_test_pos = (x, y - test_distance, z)
            if self.check_collision(ground_test_pos):
                collision_info['ground'] = True
                return
        
        collision_info['ground'] = False
    
    def snap_to_ground(self, position: Tuple[float, float, float], 
                      max_step_down: float = 1.0) -> Tuple[float, float, float]:
        """
        Snap the player to the ground with better precision and validation.
        
        Args:
            position: Current player position
            max_step_down: Maximum distance to search for ground below
            
        Returns:
            Adjusted position snapped to ground
        """
        x, y, z = position
        
        # Search for ground below current position with finer increments
        search_increment = 0.0625  # 1/16 block for precision
        search_steps = int(max_step_down / search_increment)
        
        for i in range(search_steps):
            test_y = y - (i * search_increment)
            test_pos = (x, test_y, z)
            
            # If we find a collision, we've gone into a block
            if self.check_collision(test_pos):
                # Step back up to find the surface
                surface_y = test_y + search_increment
                surface_pos = (x, surface_y, z)
                
                # Verify this is a valid position
                if not self.check_collision(surface_pos):
                    return surface_pos
                break
        
        # If no ground found within range, return original position
        return position
    
    def can_step_up(self, from_pos: Tuple[float, float, float], 
                   to_pos: Tuple[float, float, float]) -> bool:
        """
        Check if player can step up from one position to another.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            
        Returns:
            True if step-up is possible
        """
        from_x, from_y, from_z = from_pos
        to_x, to_y, to_z = to_pos
        
        y_diff = to_y - from_y
        
        # Only allow reasonable step heights
        if y_diff <= 0 or y_diff > STEP_HEIGHT:
            return False
        
        # Check if there's clearance at the target position
        return not self.check_collision(to_pos)


class MinecraftPhysics:
    """
    Improved Minecraft physics system with better movement handling.
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
        Apply gravity to vertical velocity with proper ground handling.
        
        Args:
            velocity_y: Current vertical velocity
            dt: Time delta in seconds
            on_ground: Whether the player is on ground
            
        Returns:
            New vertical velocity after gravity
        """
        if on_ground and velocity_y <= 0:
            return 0.0  # Stop falling if on ground
        
        # Apply gravity acceleration
        new_velocity = velocity_y - GRAVITY * dt
        
        # Apply terminal velocity limit
        return max(new_velocity, -TERMINAL_VELOCITY)
    
    def apply_movement_drag(self, velocity: Tuple[float, float, float], 
                           dt: float, on_ground: bool) -> Tuple[float, float, float]:
        """
        Apply movement drag/friction to velocity.
        
        Args:
            velocity: Current velocity (vx, vy, vz)
            dt: Time delta in seconds
            on_ground: Whether player is on ground
            
        Returns:
            New velocity after drag
        """
        vx, vy, vz = velocity
        
        if on_ground:
            # Ground friction
            drag_factor = 0.8 ** dt  # Exponential decay
            vx *= drag_factor
            vz *= drag_factor
        else:
            # Air resistance (much less)
            air_drag = 0.95 ** dt
            vx *= air_drag
            vz *= air_drag
        
        return vx, vy, vz
    
    def update_position(self, position: Tuple[float, float, float],
                       velocity: Tuple[float, float, float],
                       dt: float,
                       on_ground: bool,
                       jumping: bool) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], bool]:
        """
        Update player position and velocity with improved physics.
        
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
        
        # Apply movement drag
        vx, vy, vz = self.apply_movement_drag((vx, vy, vz), dt, on_ground)
        
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
        
        # If we landed on ground, snap to proper position and stop vertical movement
        if new_on_ground and not on_ground and final_vy <= 0:
            new_position = self.collision_detector.snap_to_ground(new_position)
            final_vy = 0.0
        
        return new_position, (final_vx, final_vy, final_vz), new_on_ground


# Compatibility functions for existing code (improved)
def minecraft_collide(position: Tuple[float, float, float], 
                     height: int,
                     world_blocks: Dict[Tuple[int, int, int], str]) -> Tuple[float, float, float]:
    """
    Improved compatibility function for existing collision detection code.
    
    Args:
        position: Player position to test
        height: Player height in blocks (ignored, uses standard height)
        world_blocks: World block dictionary
        
    Returns:
        Safe position after collision resolution
    """
    detector = MinecraftCollisionDetector(world_blocks)
    
    # Simple collision check and return safe position
    safe_position, _ = detector.resolve_collision(position, position)
    return safe_position


def minecraft_check_ground(position: Tuple[float, float, float],
                          world_blocks: Dict[Tuple[int, int, int], str]) -> bool:
    """
    Improved compatibility function to check if player is on ground.
    
    Args:
        position: Player position
        world_blocks: World block dictionary
        
    Returns:
        True if player is on ground
    """
    detector = MinecraftCollisionDetector(world_blocks)
    x, y, z = position
    
    # Check multiple points below current position for robust ground detection
    for test_distance in [COLLISION_EPSILON, GROUND_TOLERANCE]:
        test_position = (x, y - test_distance, z)
        if detector.check_collision(test_position):
            return True
    
    return False


def minecraft_find_spawn_point(world_blocks: Dict[Tuple[int, int, int], str],
                              search_center: Tuple[float, float] = (0.0, 0.0),
                              search_radius: int = 10) -> Optional[Tuple[float, float, float]]:
    """
    Find a safe spawn point near the given coordinates.
    
    Args:
        world_blocks: World block dictionary
        search_center: (x, z) coordinates to search around
        search_radius: Radius in blocks to search
        
    Returns:
        Safe spawn position or None if none found
    """
    detector = MinecraftCollisionDetector(world_blocks)
    center_x, center_z = search_center
    
    # Search in expanding rings from center
    for radius in range(search_radius + 1):
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if abs(dx) != radius and abs(dz) != radius and radius > 0:
                    continue  # Only check perimeter of current ring
                
                x = center_x + dx
                z = center_z + dz
                
                # Find ground level at this position
                ground_y = detector.find_ground_level(x, z)
                if ground_y is not None:
                    spawn_pos = (x, ground_y, z)
                    # Verify it's a safe spawn (no collision)
                    if not detector.check_collision(spawn_pos):
                        return spawn_pos
    
    return None
