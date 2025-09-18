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

# Collision constants - Made more restrictive to prevent block traversal
COLLISION_EPSILON = 0.0001  # Smaller value for tighter collision detection
STEP_HEIGHT = 0.5           # Reduced from 0.5625 to prevent easy block climbing  
GROUND_TOLERANCE = 0.01     # Smaller tolerance for more precise ground detection

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
    Fixed to prevent missing blocks that should be tested.
    
    Args:
        min_corner: Minimum corner of bounding box
        max_corner: Maximum corner of bounding box
        
    Returns:
        Set of block coordinates that intersect the bounding box
    """
    x_min, y_min, z_min = min_corner
    x_max, y_max, z_max = max_corner
    
    # Get integer bounds for blocks - don't add epsilon here as it can miss blocks
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
        More aggressive collision detection to prevent block traversal.
        
        Args:
            position: Player position to test
            
        Returns:
            True if collision would occur, False otherwise
        """
        # Disable cache for critical collision checks to ensure accuracy
        min_corner, max_corner = get_player_bounding_box(position)
        potential_blocks = get_blocks_in_bounding_box(min_corner, max_corner)
        
        for block_pos in potential_blocks:
            if block_pos in self.world_blocks:
                if box_intersects_block(min_corner, max_corner, block_pos):
                    return True
        
        return False
    
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
        Resolve collision with step-by-step movement AND ray-casting to prevent tunneling.
        
        CRITICAL IMPROVEMENTS TO PREVENT BLOCK TRAVERSAL:
        1. Always validate that returned positions are safe (no collision)
        2. Handle cases where old_position is already inside a block
        3. Use emergency safe position finding when normal resolution fails
        4. Multiple layers of validation to ensure players never end up inside blocks
        
        Args:
            old_position: Previous player position
            new_position: Desired new position
            
        Returns:
            Tuple of (safe_position, collision_info)
        """
        # CRITICAL FIX: First ensure old position is actually safe
        # If player is already inside a block, we need to move them to safety
        # This handles edge cases where previous physics updates left player in invalid state
        if self.check_collision(old_position):
            # Player is currently inside a block - find a safe position
            safe_pos = self._find_safe_position_near(old_position)
            if safe_pos:
                old_position = safe_pos
        
        # Check if the ray from old to new position passes through any blocks
        # This prevents high-speed tunneling through thin walls
        ray_collision, hit_block = self.ray_cast_collision(old_position, new_position)
        
        if ray_collision:
            # Ray casting detected collision, but we need to handle different movement types:
            # - Falling movement: Try to land on top of the hit block
            # - Horizontal movement: Stop at old position only if genuinely blocked
            # - Diagonal movement: Resolve component by component
            
            old_x, old_y, old_z = old_position
            new_x, new_y, new_z = new_position
            
            # Check if this is primarily a falling movement (Y decreasing significantly)
            y_movement = new_y - old_y
            horizontal_movement = math.sqrt((new_x - old_x)**2 + (new_z - old_z)**2)
            
            if y_movement < -0.5 and horizontal_movement < 0.5:
                # This is falling movement - try to land on the hit block
                if hit_block:
                    block_x, block_y, block_z = hit_block
                    # Try to place player on top of the block
                    landing_y = float(block_y + 1)  # Top surface of block
                    landing_pos = (old_x, landing_y, old_z)
                    
                    if not self.check_collision(landing_pos):
                        collision_info = {'x': False, 'y': True, 'z': False, 'ground': True}
                        return landing_pos, collision_info
            elif abs(y_movement) < 0.1:
                # This is horizontal movement - verify that target position is actually blocked
                if not self.check_collision(new_position):
                    # Target position is actually safe, ray casting may have been overly cautious
                    # Proceed with normal step-by-step resolution
                    pass  # Continue to normal resolution below
                else:
                    # Target is genuinely blocked
                    collision_info = {'x': True, 'y': False, 'z': True, 'ground': False}
                    self._update_ground_status(collision_info, old_position)
                    return old_position, collision_info
            
            # For diagonal movements or if special handling failed, return safe old position
            collision_info = {'x': True, 'y': True, 'z': True, 'ground': False}
            self._update_ground_status(collision_info, old_position)
            
            # Double-check that old_position is actually safe before returning it
            if self.check_collision(old_position):
                safe_pos = self._find_safe_position_near(old_position)
                if safe_pos:
                    old_position = safe_pos
            
            return old_position, collision_info
        
        # If ray casting is clear, proceed with normal step-by-step resolution
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        
        # Calculate movement distance
        dx = new_x - old_x
        dy = new_y - old_y
        dz = new_z - old_z
        total_distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # If movement is very large, use step-by-step collision detection
        max_step = PLAYER_WIDTH / 4  # Smaller step size for better precision
        
        if total_distance > max_step:
            # Break movement into smaller steps
            steps = int(math.ceil(total_distance / max_step))
            step_x = dx / steps
            step_y = dy / steps
            step_z = dz / steps
            
            current_x, current_y, current_z = old_x, old_y, old_z
            
            for step in range(steps):
                test_x = current_x + step_x
                test_y = current_y + step_y
                test_z = current_z + step_z
                
                # Test this step position
                step_pos, step_collision = self._resolve_single_step(
                    (current_x, current_y, current_z), 
                    (test_x, test_y, test_z)
                )
                
                # Update collision info
                for key in collision_info:
                    collision_info[key] = collision_info[key] or step_collision[key]
                
                # CRITICAL VALIDATION: Ensure step resulted in safe position
                if self.check_collision(step_pos):
                    # Step resulted in unsafe position, stop here and use current safe position
                    final_position = (current_x, current_y, current_z)
                    if self.check_collision(final_position):
                        # Even current position is unsafe, find emergency safe position
                        emergency_safe = self._find_safe_position_near(final_position)
                        if emergency_safe:
                            final_position = emergency_safe
                    return final_position, collision_info
                
                # If we hit something, stop here
                if step_collision['x'] or step_collision['y'] or step_collision['z']:
                    return step_pos, collision_info
                
                current_x, current_y, current_z = step_pos
            
            final_position = (current_x, current_y, current_z)
            
            # FINAL SAFETY CHECK for step-by-step movement
            if self.check_collision(final_position):
                emergency_safe = self._find_safe_position_near(final_position)
                if emergency_safe:
                    final_position = emergency_safe
                    collision_info['x'] = collision_info['y'] = collision_info['z'] = True
            
            return final_position, collision_info
        else:
            # Small movement, use single step
            return self._resolve_single_step(old_position, new_position)
    
    def _resolve_single_step(self, old_position: Tuple[float, float, float], 
                           new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Resolve collision for a single small step.
        CRITICAL: Always ensure the returned position is safe (no collision).
        """
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        current_x, current_y, current_z = old_x, old_y, old_z
        
        # CRITICAL FIX: Ensure starting position is safe
        if self.check_collision((current_x, current_y, current_z)):
            # Starting position is not safe, try to fix it
            safe_start = self._find_safe_position_near((current_x, current_y, current_z))
            if safe_start:
                current_x, current_y, current_z = safe_start
                collision_info['x'] = collision_info['y'] = collision_info['z'] = True
        
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
                # Try to snap to the surface of the block we hit
                ground_level = self.find_ground_level(current_x, current_z, old_y)
                if ground_level is not None:
                    test_ground_pos = (current_x, ground_level, current_z)
                    if not self.check_collision(test_ground_pos):
                        current_y = ground_level
        
        # CRITICAL VALIDATION: Final safety check
        final_position = (current_x, current_y, current_z)
        if self.check_collision(final_position):
            # Final position is still not safe! Try emergency fix
            emergency_safe = self._find_safe_position_near(final_position)
            if emergency_safe:
                final_position = emergency_safe
                collision_info['x'] = collision_info['y'] = collision_info['z'] = True
        
        # Final ground check - more robust ground detection
        self._update_ground_status(collision_info, final_position)
        
        return final_position, collision_info
    
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
    
    def ray_cast_collision(self, start_pos: Tuple[float, float, float], 
                          end_pos: Tuple[float, float, float]) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """
        Use ray casting to detect if movement from start to end would pass through any blocks.
        
        ENHANCED FOR BETTER BLOCK TRAVERSAL PREVENTION:
        - Smaller step size to catch thin walls and corner cases
        - More thorough collision checking along the path
        - Handles edge cases with floating point precision
        
        Args:
            start_pos: Starting position
            end_pos: Ending position
            
        Returns:
            Tuple of (collision_detected, first_block_hit)
        """
        sx, sy, sz = start_pos
        ex, ey, ez = end_pos
        
        # Calculate direction and distance
        dx = ex - sx
        dy = ey - sy
        dz = ez - sz
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if distance < COLLISION_EPSILON:
            return False, None
        
        # Normalize direction
        dx /= distance
        dy /= distance
        dz /= distance
        
        # IMPROVED: Use smaller step size for better precision
        # Step size should be smaller than quarter block to catch thin walls and corners
        step_size = 0.05  # Reduced from 0.1 for better collision detection
        steps = int(distance / step_size) + 1
        
        for i in range(steps + 1):
            t = min(i * step_size, distance)
            test_x = sx + dx * t
            test_y = sy + dy * t
            test_z = sz + dz * t
            
            test_pos = (test_x, test_y, test_z)
            if self.check_collision(test_pos):
                # Find which block we hit
                min_corner, max_corner = get_player_bounding_box(test_pos)
                blocks = get_blocks_in_bounding_box(min_corner, max_corner)
                
                for block_pos in blocks:
                    if block_pos in self.world_blocks:
                        if box_intersects_block(min_corner, max_corner, block_pos):
                            return True, block_pos
        
        return False, None
    
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
    
    def _find_safe_position_near(self, position: Tuple[float, float, float]) -> Optional[Tuple[float, float, float]]:
        """
        Find a safe position near the given position for players stuck inside blocks.
        
        MULTI-STRATEGY APPROACH FOR SAFETY:
        1. Find ground level and place player on top (most common case)
        2. Search upward from current position (for underground scenarios)  
        3. Search horizontally (for corner/wall stuck cases)
        
        This handles edge cases like:
        - Player teleported or spawned inside blocks
        - Physics glitches that place player in invalid position
        - Chunk loading issues that change world geometry
        
        Args:
            position: Current (unsafe) position
            
        Returns:
            Safe position or None if none found nearby
        """
        x, y, z = position
        
        # Strategy 1: Try to find ground level and place player on top
        # This is the most common case - player fell/glitched into ground
        ground_level = self.find_ground_level(x, z, y + 10.0, check_clearance=True)
        if ground_level is not None:
            safe_pos = (x, ground_level, z)
            if not self.check_collision(safe_pos):
                return safe_pos
        
        # Strategy 2: Search upward from current position
        # Handles cases where player is stuck underground or in walls
        for y_offset in [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]:
            test_pos = (x, y + y_offset, z)
            if not self.check_collision(test_pos):
                return test_pos
        
        # Strategy 3: Search in horizontal directions
        # Handles corner cases and complex geometry
        for radius in [0.5, 1.0, 1.5, 2.0]:
            for dx in [-radius, 0.0, radius]:
                for dz in [-radius, 0.0, radius]:
                    if dx == 0 and dz == 0:
                        continue
                    test_pos = (x + dx, y + 1.0, z + dz)  # Try slightly above current position
                    if not self.check_collision(test_pos):
                        return test_pos
        
        # If all else fails, return None - caller must handle this gracefully
        return None


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
