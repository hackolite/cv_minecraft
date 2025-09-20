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


def check_cube_position_occupied(position: Tuple[float, float, float], 
                                player_size: float, 
                                other_cubes: List) -> bool:
    """
    Simple check if a position is occupied by another cube to avoid complex collision calculations.
    
    Args:
        position: Position to test (x, y, z)
        player_size: Size of the player's bounding box (half-size)
        other_cubes: List of other player cubes to check against
        
    Returns:
        True if position is occupied by another cube, False otherwise
    """
    px, py, pz = position
    
    for other_cube in other_cubes:
        # Skip if not a valid cube object
        if not hasattr(other_cube, 'position') or not hasattr(other_cube, 'size'):
            continue
            
        # Get other cube's position and size
        ox, oy, oz = other_cube.position
        other_size = other_cube.size
        
        # Check 3D bounding box collision
        # Two boxes collide if they overlap in all three dimensions
        x_overlap = (px - player_size) < (ox + other_size) and (px + player_size) >= (ox - other_size)
        y_overlap = (py - player_size) < (oy + other_size) and (py + player_size) >= (oy - other_size)
        z_overlap = (pz - player_size) < (oz + other_size) and (pz + player_size) >= (oz - other_size)
        
        if x_overlap and y_overlap and z_overlap:
            return True
    
    return False


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
        self.other_cubes = []  # List of other player cubes to check against
        
    def set_other_cubes(self, other_cubes: List) -> None:
        """
        Set the list of other player cubes to check for position conflicts.
        
        Args:
            other_cubes: List of other player cubes
        """
        self.other_cubes = other_cubes if other_cubes else []
        
    def _cache_key(self, position: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Generate cache key for position (rounded to avoid float precision issues)"""
        x, y, z = position
        return (round(x * 1000), round(y * 1000), round(z * 1000))
    
    def check_collision(self, position: Tuple[float, float, float]) -> bool:
        """
        Check if the player would collide with any blocks or other cubes at the given position.
        First checks for cube position conflicts (simple check), then block collisions if needed.
        
        Args:
            position: Player position to test
            
        Returns:
            True if collision would occur, False otherwise
        """
        # First, simple check if position is occupied by another cube
        # This avoids complex collision calculations when cubes are in same position
        if check_cube_position_occupied(position, PLAYER_WIDTH / 2, self.other_cubes):
            return True
        
        # If no cube collision, proceed with normal block collision detection
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
        Resolve collision with improved diagonal movement handling.
        Uses sliding collision response instead of hard blocking for minor collisions.
        Enhanced to prevent diagonal tunneling through block corners.
        
        Args:
            old_position: Previous player position
            new_position: Desired new position
            
        Returns:
            Tuple of (safe_position, collision_info)
        """
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        # Check if this is a diagonal movement (both X and Z changing significantly)
        dx = abs(new_x - old_x)
        dz = abs(new_z - old_z)
        is_diagonal = dx > COLLISION_EPSILON and dz > COLLISION_EPSILON
        
        # For diagonal movements, first check if the path would go through any blocks
        if is_diagonal:
            ray_collision, hit_block = self.ray_cast_collision(old_position, new_position)
            if ray_collision:
                # Diagonal movement would tunnel through blocks - use conservative sliding
                return self._resolve_with_conservative_sliding(old_position, new_position)
        
        # Try the movement with axis-separated collision resolution (simplest implementation)
        return self._resolve_with_axis_separation(old_position, new_position)
    
    def _resolve_with_sliding(self, old_position: Tuple[float, float, float], 
                             new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Resolve collision with sliding behavior for diagonal movement.
        Instead of stopping on minor collisions, tries to slide along walls.
        Handles corner clipping by allowing small adjustments.
        Enhanced with better sliding logic.
        """
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        current_x, current_y, current_z = old_x, old_y, old_z
        
        # First try the full movement
        if not self.check_collision(new_position):
            self._update_ground_status(collision_info, new_position)
            return new_position, collision_info
        
        # If full movement fails, check if it's a minor corner collision
        # that can be resolved by small position adjustments
        adjusted_position = self._try_corner_adjustment(old_position, new_position)
        if adjusted_position and not self.check_collision(adjusted_position):
            self._update_ground_status(collision_info, adjusted_position)
            return adjusted_position, collision_info
        
        # If corner adjustment doesn't work, try progressive sliding
        # This approach tries to maintain as much movement as possible
        
        # Calculate movement distances
        dx = new_x - old_x
        dy = new_y - old_y
        dz = new_z - old_z
        
        # Try different sliding strategies
        best_position = old_position
        best_distance = 0.0
        
        # Strategy 1: Try X then Z
        test_pos = self._try_axis_sliding(old_position, new_position, ['x', 'z', 'y'])
        distance = self._calculate_distance(old_position, test_pos)
        if distance > best_distance:
            best_position = test_pos
            best_distance = distance
        
        # Strategy 2: Try Z then X  
        test_pos = self._try_axis_sliding(old_position, new_position, ['z', 'x', 'y'])
        distance = self._calculate_distance(old_position, test_pos)
        if distance > best_distance:
            best_position = test_pos
            best_distance = distance
        
        # Strategy 3: Try partial movement in each axis
        test_pos = self._try_partial_sliding(old_position, new_position)
        distance = self._calculate_distance(old_position, test_pos)
        if distance > best_distance:
            best_position = test_pos
            best_distance = distance
        
        # Update collision info based on what was blocked
        collision_info['x'] = abs(best_position[0] - new_x) > COLLISION_EPSILON
        collision_info['z'] = abs(best_position[2] - new_z) > COLLISION_EPSILON
        collision_info['y'] = abs(best_position[1] - new_y) > COLLISION_EPSILON
        
        if collision_info['y'] and new_y < old_y:
            collision_info['ground'] = True
        
        # Update ground status
        self._update_ground_status(collision_info, best_position)
        
        return best_position, collision_info
    
    def _resolve_with_axis_separation(self, old_position: Tuple[float, float, float], 
                                    new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Resolve collision using simple axis-separated collision detection.
        Implements the simplest possible approach as specified in the problem statement:
        - Process axes separately in order: X → Y → Z
        - Block movement and reset velocity on collision
        - Handle ground snapping for Y axis
        
        Args:
            old_position: Previous player position
            new_position: Desired new position
            
        Returns:
            Tuple of (safe_position, collision_info)
        """
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        # Start with old position and process each axis separately
        current_x, current_y, current_z = old_x, old_y, old_z
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        
        # AXIS X (left/right): Attempt movement, block if collision, set vx = 0
        # Test X movement at the ORIGINAL Y and Z positions to ensure independence
        test_position_x = (new_x, old_y, old_z)
        if not self.check_collision(test_position_x):
            current_x = new_x  # Movement allowed
        else:
            collision_info['x'] = True  # Block movement, vx will be set to 0
        
        # AXIS Y (vertical): Add gravity, handle ground/ceiling collisions
        # For Y axis, we need to check the movement path, not just the destination
        if new_y != old_y:
            # Check collision at destination first
            test_position_y = (current_x, new_y, current_z)
            collision_at_destination = self.check_collision(test_position_y)
            
            if new_y > old_y:
                # Moving upward - check for ceiling collisions along the path
                if not collision_at_destination:
                    step_size = 0.1
                    steps = int(abs(new_y - old_y) / step_size) + 1
                    collision_found = False
                    collision_y = new_y
                    
                    for i in range(1, steps + 1):
                        test_y = old_y + (new_y - old_y) * i / steps
                        test_pos = (current_x, test_y, current_z)
                        if self.check_collision(test_pos):
                            collision_found = True
                            collision_y = test_y
                            break
                    
                    if collision_found:
                        collision_info['y'] = True
                        # Stop just before the collision point
                        current_y = max(old_y, collision_y - 0.1)
                    else:
                        current_y = new_y  # Movement allowed
                else:
                    # Collision at destination
                    collision_info['y'] = True
                    current_y = old_y  # Stop at old position
            else:
                # Moving downward - check if we would pass through any solid blocks
                # and find where to land
                ground_level = self.find_ground_level(current_x, current_z, old_y)
                
                if ground_level is not None and new_y < ground_level:
                    # We would go below ground level - land on the ground
                    collision_info['y'] = True
                    collision_info['ground'] = True
                    current_y = ground_level
                else:
                    # No ground in the way, or destination is above ground
                    current_y = new_y  # Movement allowed
        else:
            current_y = old_y  # No Y movement requested
        
        # AXIS Z (forward/backward): Same logic as X axis
        # Test Z movement at the ORIGINAL Y position to ensure independence from Y changes
        test_position_z = (current_x, old_y, new_z)
        if not self.check_collision(test_position_z):
            current_z = new_z  # Movement allowed
        else:
            collision_info['z'] = True  # Block movement, vz will be set to 0
        
        final_position = (current_x, current_y, current_z)
        
        # Update ground status for final position
        self._update_ground_status(collision_info, final_position)
        
        return final_position, collision_info
    
    def _resolve_with_conservative_sliding(self, old_position: Tuple[float, float, float], 
                                         new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Resolve collision with conservative sliding that prevents diagonal tunneling.
        This method ensures that diagonal movements cannot pass through block corners.
        
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
        
        # For diagonal movements that would tunnel, try conservative sliding:
        # Only allow movement in one axis at a time, with path validation
        
        # Try X movement first, with path validation
        if abs(new_x - old_x) > COLLISION_EPSILON:
            test_x_pos = (new_x, current_y, current_z)
            # Check both destination and path for X movement
            x_ray_collision, _ = self.ray_cast_collision((current_x, current_y, current_z), test_x_pos)
            if not self.check_collision(test_x_pos) and not x_ray_collision:
                current_x = new_x
            else:
                collision_info['x'] = True
        
        # Try Z movement second, with path validation
        if abs(new_z - old_z) > COLLISION_EPSILON:
            test_z_pos = (current_x, current_y, new_z)
            # Check both destination and path for Z movement
            z_ray_collision, _ = self.ray_cast_collision((current_x, current_y, current_z), test_z_pos)
            if not self.check_collision(test_z_pos) and not z_ray_collision:
                current_z = new_z
            else:
                collision_info['z'] = True
        
        # Handle Y movement last (same as axis separation)
        if new_y != old_y:
            test_position_y = (current_x, new_y, current_z)
            collision_at_destination = self.check_collision(test_position_y)
            
            if new_y > old_y:
                # Moving upward - check for ceiling collisions along the path
                if not collision_at_destination:
                    step_size = 0.1
                    steps = int(abs(new_y - old_y) / step_size) + 1
                    collision_found = False
                    collision_y = new_y
                    
                    for i in range(1, steps + 1):
                        test_y = old_y + (new_y - old_y) * i / steps
                        test_pos = (current_x, test_y, current_z)
                        if self.check_collision(test_pos):
                            collision_found = True
                            collision_y = test_y
                            break
                    
                    if collision_found:
                        collision_info['y'] = True
                        current_y = max(old_y, collision_y - 0.1)
                    else:
                        current_y = new_y
                else:
                    collision_info['y'] = True
                    current_y = old_y
            else:
                # Moving downward
                ground_level = self.find_ground_level(current_x, current_z, old_y)
                if ground_level is not None and new_y < ground_level:
                    collision_info['y'] = True
                    collision_info['ground'] = True
                    current_y = ground_level
                else:
                    current_y = new_y
        else:
            current_y = old_y
        
        final_position = (current_x, current_y, current_z)
        self._update_ground_status(collision_info, final_position)
        
        return final_position, collision_info
    
    def _try_axis_sliding(self, old_position: Tuple[float, float, float], 
                         new_position: Tuple[float, float, float], 
                         axis_order: List[str]) -> Tuple[float, float, float]:
        """Try sliding along axes in the specified order."""
        current_x, current_y, current_z = old_position
        new_x, new_y, new_z = new_position
        
        for axis in axis_order:
            if axis == 'x':
                test_pos = (new_x, current_y, current_z)
                if not self.check_collision(test_pos):
                    current_x = new_x
            elif axis == 'z':
                test_pos = (current_x, current_y, new_z)
                if not self.check_collision(test_pos):
                    current_z = new_z
            elif axis == 'y':
                test_pos = (current_x, new_y, current_z)
                if not self.check_collision(test_pos):
                    current_y = new_y
                else:
                    # Handle ground snapping for Y collisions
                    if new_y < old_position[1]:
                        ground_level = self.find_ground_level(current_x, current_z, old_position[1])
                        if ground_level is not None:
                            current_y = ground_level
        
        return (current_x, current_y, current_z)
    
    def _try_partial_sliding(self, old_position: Tuple[float, float, float], 
                            new_position: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Try moving partially in each direction to maximize movement."""
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        # Calculate movement deltas
        dx = new_x - old_x
        dy = new_y - old_y
        dz = new_z - old_z
        
        # Try different percentages of movement
        for factor in [0.9, 0.8, 0.7, 0.6, 0.5]:
            test_x = old_x + dx * factor
            test_y = old_y + dy * factor
            test_z = old_z + dz * factor
            
            test_pos = (test_x, test_y, test_z)
            if not self.check_collision(test_pos):
                return test_pos
        
        return old_position
    
    def _calculate_distance(self, pos1: Tuple[float, float, float], 
                           pos2: Tuple[float, float, float]) -> float:
        """Calculate 3D distance between two positions."""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        dz = pos2[2] - pos1[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _try_corner_adjustment(self, old_position: Tuple[float, float, float], 
                              new_position: Tuple[float, float, float]) -> Optional[Tuple[float, float, float]]:
        """
        Try to adjust position slightly to avoid corner clipping during diagonal movement.
        This helps with the issue where player gets stuck on block corners.
        Enhanced version with better adjustment strategies.
        """
        old_x, old_y, old_z = old_position
        new_x, new_y, new_z = new_position
        
        # Calculate movement direction
        dx = new_x - old_x
        dy = new_y - old_y
        dz = new_z - old_z
        
        # Only apply corner adjustment for diagonal movement
        if abs(dx) < COLLISION_EPSILON or abs(dz) < COLLISION_EPSILON:
            return None
        
        # Try progressively larger adjustments
        adjustment_distances = [0.02, 0.05, 0.1, 0.15]  # Multiple adjustment sizes
        
        for adjustment_distance in adjustment_distances:
            # Strategy 1: Try adjusting perpendicular to movement direction
            # Calculate perpendicular directions
            movement_length = math.sqrt(dx*dx + dz*dz)
            if movement_length > 0:
                # Normalized movement direction
                move_x = dx / movement_length
                move_z = dz / movement_length
                
                # Perpendicular directions (rotate 90 degrees)
                perp_x = -move_z
                perp_z = move_x
                
                # Try adjusting perpendicular to movement
                for direction in [-1, 1]:
                    adj_x = perp_x * direction * adjustment_distance
                    adj_z = perp_z * direction * adjustment_distance
                    test_pos = (new_x + adj_x, new_y, new_z + adj_z)
                    
                    if not self.check_collision(test_pos):
                        return test_pos
            
            # Strategy 2: Try cardinal direction adjustments
            for x_adj in [-adjustment_distance, 0, adjustment_distance]:
                for z_adj in [-adjustment_distance, 0, adjustment_distance]:
                    if x_adj == 0 and z_adj == 0:
                        continue
                    
                    test_pos = (new_x + x_adj, new_y, new_z + z_adj)
                    if not self.check_collision(test_pos):
                        return test_pos
            
            # Strategy 3: Try backing off slightly in movement direction
            back_off_factor = adjustment_distance / movement_length if movement_length > 0 else 0
            if back_off_factor < 0.5:  # Don't back off too much
                test_pos = (new_x - dx * back_off_factor, new_y, new_z - dz * back_off_factor)
                if not self.check_collision(test_pos):
                    return test_pos
        
        return None
    
    def _resolve_single_step(self, old_position: Tuple[float, float, float], 
                           new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Resolve collision for a single small step.
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
    
    def ray_cast_collision(self, start_pos: Tuple[float, float, float], 
                          end_pos: Tuple[float, float, float]) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """
        Use ray casting to detect if movement from start to end would pass through any blocks.
        This prevents tunneling through thin walls or fast movement.
        Enhanced with better precision for diagonal movements.
        
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
        
        # Use smaller step size for diagonal movements to catch corner collisions
        is_diagonal = abs(dx) > 0.1 and abs(dz) > 0.1
        step_size = 0.05 if is_diagonal else 0.1  # Smaller steps for diagonal movement
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
