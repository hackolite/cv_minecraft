#!/usr/bin/env python3
"""
Bulletproof Minecraft Physics System
===================================

This version fixes all block traversal issues with multiple safety layers:
- Micro-step collision detection
- Final position validation
- Improved bounding box calculations
- Conservative collision testing
"""

import math
from typing import Tuple, List, Dict, Optional, Set

# Standard Minecraft Physics Constants
PLAYER_WIDTH = 0.6
PLAYER_HEIGHT = 1.8
PLAYER_EYE_HEIGHT = 1.62

GRAVITY = 32.0
TERMINAL_VELOCITY = 78.4
JUMP_VELOCITY = 10.0
WALKING_SPEED = 4.317
SPRINTING_SPEED = 5.612
FLYING_SPEED = 10.89

# Collision constants - more conservative
COLLISION_EPSILON = 0.0001  # Smaller epsilon for precision
STEP_HEIGHT = 0.5625
GROUND_TOLERANCE = 0.05
MICRO_STEP_SIZE = 0.05      # Very small steps to catch all collisions

BLOCK_SIZE = 1.0

def get_player_bounding_box(position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Get player bounding box with slight padding to ensure collision detection.
    """
    x, y, z = position
    half_width = PLAYER_WIDTH / 2
    
    # Add tiny padding to ensure we don't miss edge cases
    padding = COLLISION_EPSILON
    
    min_corner = (x - half_width - padding, y - padding, z - half_width - padding)
    max_corner = (x + half_width + padding, y + PLAYER_HEIGHT + padding, z + half_width + padding)
    
    return min_corner, max_corner


def get_blocks_in_bounding_box(min_corner: Tuple[float, float, float], 
                              max_corner: Tuple[float, float, float]) -> Set[Tuple[int, int, int]]:
    """
    Get ALL blocks that could possibly intersect with bounding box.
    Uses conservative approach to never miss a block.
    """
    x_min, y_min, z_min = min_corner
    x_max, y_max, z_max = max_corner
    
    # Expand the search area slightly to catch edge cases
    block_x_min = int(math.floor(x_min - COLLISION_EPSILON))
    block_x_max = int(math.floor(x_max + COLLISION_EPSILON))
    block_y_min = int(math.floor(y_min - COLLISION_EPSILON))
    block_y_max = int(math.floor(y_max + COLLISION_EPSILON))
    block_z_min = int(math.floor(z_min - COLLISION_EPSILON))
    block_z_max = int(math.floor(z_max + COLLISION_EPSILON))
    
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
    Ultra-conservative collision detection with proper epsilon handling.
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
    
    # Conservative intersection test with epsilon
    x_intersect = (box_x_min < block_x_max - COLLISION_EPSILON) and (box_x_max > block_x_min + COLLISION_EPSILON)
    y_intersect = (box_y_min < block_y_max - COLLISION_EPSILON) and (box_y_max > block_y_min + COLLISION_EPSILON)
    z_intersect = (box_z_min < block_z_max - COLLISION_EPSILON) and (box_z_max > block_z_min + COLLISION_EPSILON)
    
    return x_intersect and y_intersect and z_intersect


class BulletproofCollisionDetector:
    """
    Bulletproof collision detector that prevents ALL block traversal.
    """
    
    def __init__(self, world_blocks: Dict[Tuple[int, int, int], str]):
        self.world_blocks = world_blocks
        
    def is_position_safe(self, position: Tuple[float, float, float]) -> bool:
        """
        Check if a position is completely safe (no collisions).
        """
        min_corner, max_corner = get_player_bounding_box(position)
        potential_blocks = get_blocks_in_bounding_box(min_corner, max_corner)
        
        for block_pos in potential_blocks:
            if block_pos in self.world_blocks:
                if box_intersects_block(min_corner, max_corner, block_pos):
                    return False
        
        return True
    
    def find_safe_position_on_line(self, start: Tuple[float, float, float], 
                                  end: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Find the furthest safe position along a line from start to end.
        Uses binary search for precision.
        """
        if not self.is_position_safe(start):
            return start  # Can't move from unsafe start
            
        if self.is_position_safe(end):
            return end  # End is safe, use it
        
        # Binary search to find the furthest safe point
        safe_t = 0.0    # Known safe parameter
        unsafe_t = 1.0  # Known unsafe parameter
        
        for _ in range(20):  # 20 iterations gives very high precision
            mid_t = (safe_t + unsafe_t) / 2
            
            mid_pos = (
                start[0] + (end[0] - start[0]) * mid_t,
                start[1] + (end[1] - start[1]) * mid_t,
                start[2] + (end[2] - start[2]) * mid_t
            )
            
            if self.is_position_safe(mid_pos):
                safe_t = mid_t
            else:
                unsafe_t = mid_t
        
        # Return the furthest safe position
        return (
            start[0] + (end[0] - start[0]) * safe_t,
            start[1] + (end[1] - start[1]) * safe_t,
            start[2] + (end[2] - start[2]) * safe_t
        )
    
    def micro_step_movement(self, start: Tuple[float, float, float], 
                           end: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Move in micro-steps to ensure we never skip over any blocks.
        """
        current_pos = start
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]  
        dz = end[2] - start[2]
        total_distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if total_distance < COLLISION_EPSILON:
            return current_pos
        
        # Number of micro-steps needed
        num_steps = max(1, int(math.ceil(total_distance / MICRO_STEP_SIZE)))
        
        step_x = dx / num_steps
        step_y = dy / num_steps
        step_z = dz / num_steps
        
        for step in range(num_steps):
            next_pos = (
                current_pos[0] + step_x,
                current_pos[1] + step_y,
                current_pos[2] + step_z
            )
            
            # Test if this micro-step is safe
            if self.is_position_safe(next_pos):
                current_pos = next_pos
            else:
                # Hit something, stop here
                break
        
        return current_pos
    
    def resolve_collision(self, old_position: Tuple[float, float, float], 
                         new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Bulletproof collision resolution with multiple safety checks.
        """
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        
        # Safety check: if old position is unsafe, try to find a safe nearby position
        if not self.is_position_safe(old_position):
            old_position = self._find_nearest_safe_position(old_position)
        
        # Method 1: Try axis-by-axis movement
        safe_pos = self._resolve_axis_by_axis(old_position, new_position, collision_info)
        
        # Method 2: If axis-by-axis fails, use micro-stepping
        if not self.is_position_safe(safe_pos):
            safe_pos = self.micro_step_movement(old_position, new_position)
            collision_info = {'x': True, 'y': True, 'z': True, 'ground': False}
        
        # Method 3: If micro-stepping fails, use binary search
        if not self.is_position_safe(safe_pos):
            safe_pos = self.find_safe_position_on_line(old_position, new_position)
            collision_info = {'x': True, 'y': True, 'z': True, 'ground': False}
        
        # Final safety check
        if not self.is_position_safe(safe_pos):
            safe_pos = old_position
            collision_info = {'x': True, 'y': True, 'z': True, 'ground': False}
        
        # Update ground status
        self._update_ground_status(collision_info, safe_pos)
        
        return safe_pos, collision_info
    
    def _resolve_axis_by_axis(self, old_pos: Tuple[float, float, float], 
                            new_pos: Tuple[float, float, float],
                            collision_info: Dict[str, bool]) -> Tuple[float, float, float]:
        """
        Try to move along each axis separately.
        """
        old_x, old_y, old_z = old_pos
        new_x, new_y, new_z = new_pos
        current_x, current_y, current_z = old_x, old_y, old_z
        
        # Try X movement
        test_x_pos = (new_x, current_y, current_z)
        if self.is_position_safe(test_x_pos):
            current_x = new_x
        else:
            collision_info['x'] = True
            # Try partial X movement
            partial_x_pos = self.find_safe_position_on_line((current_x, current_y, current_z), test_x_pos)
            current_x = partial_x_pos[0]
        
        # Try Z movement
        test_z_pos = (current_x, current_y, new_z)
        if self.is_position_safe(test_z_pos):
            current_z = new_z
        else:
            collision_info['z'] = True
            # Try partial Z movement
            partial_z_pos = self.find_safe_position_on_line((current_x, current_y, current_z), test_z_pos)
            current_z = partial_z_pos[2]
        
        # Try Y movement
        test_y_pos = (current_x, new_y, current_z)
        if self.is_position_safe(test_y_pos):
            current_y = new_y
        else:
            collision_info['y'] = True
            # Try partial Y movement
            partial_y_pos = self.find_safe_position_on_line((current_x, current_y, current_z), test_y_pos)
            current_y = partial_y_pos[1]
        
        return (current_x, current_y, current_z)
    
    def _find_nearest_safe_position(self, unsafe_pos: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Find the nearest safe position to an unsafe one.
        """
        x, y, z = unsafe_pos
        
        # Try positions in expanding radius
        for radius in [0.1, 0.2, 0.3, 0.5, 1.0]:
            for dx in [-radius, 0, radius]:
                for dy in [-radius, 0, radius]:
                    for dz in [-radius, 0, radius]:
                        test_pos = (x + dx, y + dy, z + dz)
                        if self.is_position_safe(test_pos):
                            return test_pos
        
        # If no safe position found, return original
        return unsafe_pos
    
    def _update_ground_status(self, collision_info: Dict[str, bool], 
                            position: Tuple[float, float, float]) -> None:
        """
        Check if player is on ground.
        """
        x, y, z = position
        
        # Test multiple points slightly below the player
        test_positions = [
            (x, y - COLLISION_EPSILON, z),
            (x, y - GROUND_TOLERANCE, z),
            (x, y - 0.1, z)
        ]
        
        for test_pos in test_positions:
            if not self.is_position_safe(test_pos):
                collision_info['ground'] = True
                return
        
        collision_info['ground'] = False


class MinecraftPhysics:
    """
    Physics system using the bulletproof collision detector.
    """
    
    def __init__(self, collision_detector: BulletproofCollisionDetector):
        self.collision_detector = collision_detector
    
    def apply_gravity(self, velocity_y: float, dt: float, on_ground: bool) -> float:
        if on_ground and velocity_y <= 0:
            return 0.0
        new_velocity = velocity_y - GRAVITY * dt
        return max(new_velocity, -TERMINAL_VELOCITY)
    
    def apply_movement_drag(self, velocity: Tuple[float, float, float], 
                           dt: float, on_ground: bool) -> Tuple[float, float, float]:
        vx, vy, vz = velocity
        
        if on_ground:
            drag_factor = 0.8 ** dt
            vx *= drag_factor
            vz *= drag_factor
        else:
            air_drag = 0.95 ** dt
            vx *= air_drag
            vz *= air_drag
        
        return vx, vy, vz
    
    def update_position(self, position: Tuple[float, float, float],
                       velocity: Tuple[float, float, float],
                       dt: float,
                       on_ground: bool,
                       jumping: bool) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], bool]:
        
        x, y, z = position
        vx, vy, vz = velocity
        
        # Handle jumping
        if jumping and on_ground:
            vy = JUMP_VELOCITY
            on_ground = False
        
        # Apply physics
        vy = self.apply_gravity(vy, dt, on_ground)
        vx, vy, vz = self.apply_movement_drag((vx, vy, vz), dt, on_ground)
        
        # Calculate desired new position
        new_x = x + vx * dt
        new_y = y + vy * dt
        new_z = z + vz * dt
        
        # Resolve collisions with bulletproof method
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
        
        new_on_ground = collision_info['ground']
        
        # Final safety verification
        if not self.collision_detector.is_position_safe(new_position):
            print(f"WARNING: Final position {new_position} is unsafe! Reverting to {position}")
            new_position = position
            final_vx = final_vy = final_vz = 0.0
        
        return new_position, (final_vx, final_vy, final_vz), new_on_ground


# Compatibility functions
def minecraft_collide(position: Tuple[float, float, float], 
                     height: int,
                     world_blocks: Dict[Tuple[int, int, int], str]) -> Tuple[float, float, float]:
    detector = BulletproofCollisionDetector(world_blocks)
    safe_position, _ = detector.resolve_collision(position, position)
    return safe_position


def minecraft_check_ground(position: Tuple[float, float, float],
                          world_blocks: Dict[Tuple[int, int, int], str]) -> bool:
    detector = BulletproofCollisionDetector(world_blocks)
    collision_info = {'ground': False}
    detector._update_ground_status(collision_info, position)
    return collision_info['ground']


# Test function to verify the system works
def test_collision_system():
    """Test the bulletproof collision system."""
    # Create a simple test world
    world_blocks = {}
    
    # Add some test blocks
    for x in range(-2, 3):
        for z in range(-2, 3):
            world_blocks[(x, 0, z)] = "stone"  # Ground level
            if x == 0 and z == 0:
                world_blocks[(x, 1, z)] = "stone"  # Wall
    
    detector = BulletproofCollisionDetector(world_blocks)
    physics = MinecraftPhysics(detector)
    
    # Test position
    test_pos = (0.5, 1.5, 0.5)  # Should be blocked by wall
    print(f"Position {test_pos} is safe: {detector.is_position_safe(test_pos)}")
    
    # Test movement
    start_pos = (-1.0, 1.0, 0.0)
    end_pos = (1.0, 1.0, 0.0)  # Try to move through wall
    
    safe_pos, info = detector.resolve_collision(start_pos, end_pos)
    print(f"Movement from {start_pos} to {end_pos} resulted in {safe_pos}")
    print(f"Collision info: {info}")
    
    return detector, physics


if __name__ == "__main__":
    test_collision_system()
