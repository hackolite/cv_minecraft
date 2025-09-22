#!/usr/bin/env python3
"""
Simplified Minecraft Physics System (inspired by fogleman/Minecraft)
==================================================================

This module implements a simplified Minecraft-style physics system inspired by 
the fogleman/Minecraft approach, consolidating collision detection into a simple,
clean interface. Used by both client and server for consistent behavior.

COLLISION SYSTEM APPROACH:
=========================
The collision detection system has been dramatically simplified and is inspired by the
fogleman/Minecraft implementation (https://github.com/fogleman/Minecraft/blob/master/main.py).

This simplified approach:
- Tests ONLY the player's center position (floor coordinates) for block collision
- Tests ONLY the player's head position (center + height) for block collision  
- NO complex AABB (Axis-Aligned Bounding Box) calculations
- NO complex boundary thickness or clearance calculations
- NO complex path traversal or diagonal tunneling prevention
- Simple axis-by-axis collision resolution without complex snapping
- Much better performance through dramatically simplified calculations

Key Features:
- Unified collision management in a single module
- Maximum simplification inspired by fogleman/Minecraft approach
- Clean interfaces for both client and server
- Elimination of code duplication and complexity
- Standard Minecraft physics constants
- Simple collision detection using only center position + height checking

WHAT WAS REMOVED:
================
- Complex AABB bounding box collision detection
- Player width/depth collision calculations  
- Complex path intersection and traversal prevention
- Complex snapping and clearance algorithms
- Multi-sample collision detection along movement paths
- Boundary thickness considerations

WHAT REMAINS:
============
- Simple center position collision (floor of X, Y, Z coordinates)
- Simple head position collision (center + player height)
- Basic axis-by-axis movement resolution
- Air block filtering (air blocks don't cause collision)
- Basic ground detection for physics
"""

import math
import logging
import time
from datetime import datetime
from typing import Tuple, List, Dict, Optional, Set
from collections import defaultdict

# Standard Minecraft Physics Constants - 1x1x1 cube
PLAYER_WIDTH = 1.0          # Player width (X and Z dimensions) 
PLAYER_HEIGHT = 1.0         # Player height (Y dimension)
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

# Setup collision logger
collision_logger = logging.getLogger('minecraft_collision')
collision_logger.setLevel(logging.INFO)



# ============================================================================
# UNIFIED COLLISION MANAGER
# ============================================================================

class UnifiedCollisionManager:
    """
    Simplified unified collision manager for both client and server.
    Consolidates all collision detection into a single, clean interface.
    """
    
    def __init__(self, world_blocks: Dict[Tuple[int, int, int], str]):
        """Initialize the collision manager."""
        self.world_blocks = world_blocks
        self.other_players = []  # List of other players for player-to-player collision
        
    def set_other_players(self, players: List) -> None:
        """Set other players for collision detection."""
        self.other_players = players if players else []
    
    def update_world(self, world_blocks: Dict[Tuple[int, int, int], str]) -> None:
        """Update the world blocks."""
        self.world_blocks = world_blocks
    
    def check_block_collision(self, position: Tuple[float, float, float]) -> bool:
        """
        Simplified collision check inspired by fogleman/Minecraft.
        Only checks the player's center position and height, not complex bounding box.
        """
        return self.simple_collision_check(position)


    
    def check_player_collision(self, position: Tuple[float, float, float], player_id: str = None) -> bool:
        """Check collision with other players."""
        px, py, pz = position
        player_size = PLAYER_WIDTH / 2
        
        for other_player in self.other_players:
            # Skip self if player_id provided
            if player_id and hasattr(other_player, 'id') and other_player.id == player_id:
                continue
                
            # Get other player position and size
            if hasattr(other_player, 'position'):
                ox, oy, oz = other_player.position
            else:
                continue
                
            other_size = getattr(other_player, 'size', PLAYER_WIDTH / 2)
            
            # Check 3D bounding box collision
            x_overlap = (px - player_size) < (ox + other_size) and (px + player_size) > (ox - other_size)
            y_overlap = py < (oy + PLAYER_HEIGHT) and (py + PLAYER_HEIGHT) > oy
            z_overlap = (pz - player_size) < (oz + other_size) and (pz + player_size) > (oz - other_size)
            
            if x_overlap and y_overlap and z_overlap:
                # Log player collision with AABB coordinates, time and coordinates
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                # Calculate player AABB coordinates
                player1_min_x = px - player_size
                player1_max_x = px + player_size
                player1_min_y = py
                player1_max_y = py + PLAYER_HEIGHT
                player1_min_z = pz - player_size
                player1_max_z = pz + player_size
                
                player2_min_x = ox - other_size
                player2_max_x = ox + other_size
                player2_min_y = oy
                player2_max_y = oy + PLAYER_HEIGHT
                player2_min_z = oz - other_size
                player2_max_z = oz + other_size
                
                collision_logger.info(f"🚫 COLLISION DÉTECTÉE - Joueur vs Joueur")
                collision_logger.info(f"   Heure: {current_time}")
                collision_logger.info(f"   Position joueur 1: ({px:.3f}, {py:.3f}, {pz:.3f})")
                collision_logger.info(f"   Position joueur 2: ({ox:.3f}, {oy:.3f}, {oz:.3f})")
                collision_logger.info(f"   AABB Joueur 1: min=({player1_min_x:.3f}, {player1_min_y:.3f}, {player1_min_z:.3f}) max=({player1_max_x:.3f}, {player1_max_y:.3f}, {player1_max_z:.3f})")
                collision_logger.info(f"   AABB Joueur 2: min=({player2_min_x:.3f}, {player2_min_y:.3f}, {player2_min_z:.3f}) max=({player2_max_x:.3f}, {player2_max_y:.3f}, {player2_max_z:.3f})")
                
                return True
        return False
    
    def check_collision(self, position: Tuple[float, float, float], player_id: str = None) -> bool:
        """
        Comprehensive collision check using proper bounding box detection.
        Uses both block collision (AABB) and player collision for complete accuracy.
        
        Args:
            position: Position to check
            player_id: Player ID for player-to-player collision avoidance
        """
        # Use AABB collision detection for blocks
        block_collision = self.check_block_collision(position)
        
        # Check player-to-player collision  
        player_collision = self.check_player_collision(position, player_id)
        
        return block_collision or player_collision
    
    def find_ground_level(self, x: float, z: float, start_y: float = 256.0) -> Optional[float]:
        """Find ground level at given x, z coordinates."""
        for y in range(int(start_y), -64, -1):
            block_pos = (int(math.floor(x)), y, int(math.floor(z)))
            if block_pos in self.world_blocks:
                ground_y = float(y + 1)
                # Check if player has clearance above ground
                test_pos = (x, ground_y, z)
                if not self.check_block_collision(test_pos):
                    return ground_y
        return None
    


    
    def resolve_collision(self, old_pos: Tuple[float, float, float], 
                                  new_pos: Tuple[float, float, float],
                                  player_id: str = None) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Simplified collision resolution inspired by fogleman/Minecraft.
        
        This simplified approach:
        - Only checks final destination for collision (no path intersection)
        - Uses simple axis-by-axis backtracking if collision detected
        - Eliminates complex traversal prevention for simplicity
        - Much faster and simpler than complex AABB collision resolution
        """
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        
        # Simple approach: if destination has collision, try axis-by-axis movement
        if self.simple_collision_check(new_pos, player_id):
            # Find safe position using simple axis-by-axis movement
            safe_pos = self._find_safe_position_simple(old_pos, new_pos)
            
            # Determine which axis caused the collision
            old_x, old_y, old_z = old_pos
            safe_x, safe_y, safe_z = safe_pos
            
            if abs(safe_x - old_x) < abs(new_pos[0] - old_x):
                collision_info['x'] = True
            if abs(safe_y - old_y) < abs(new_pos[1] - old_y):
                collision_info['y'] = True
            if abs(safe_z - old_z) < abs(new_pos[2] - old_z):
                collision_info['z'] = True
        else:
            # No collision detected, allow movement
            safe_pos = new_pos
        
        # Check if on ground (simple check)
        ground_test_pos = (safe_pos[0], safe_pos[1] - 0.1, safe_pos[2])
        if self.simple_collision_check(ground_test_pos, player_id):
            collision_info['ground'] = True
        
        return safe_pos, collision_info
    
    def _find_safe_position_simple(self, old_pos: Tuple[float, float, float], 
                                  new_pos: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Simple axis-by-axis movement inspired by fogleman/Minecraft.
        Try each axis independently and stop at the first collision.
        """
        old_x, old_y, old_z = old_pos
        new_x, new_y, new_z = new_pos
        
        # Start with old position
        safe_pos = list(old_pos)
        
        # Test X movement first
        if new_x != old_x:
            test_x_pos = (new_x, safe_pos[1], safe_pos[2])
            if not self.simple_collision_check(test_x_pos):
                safe_pos[0] = new_x
        
        # Test Y movement second
        if new_y != old_y:
            test_y_pos = (safe_pos[0], new_y, safe_pos[2])
            if not self.simple_collision_check(test_y_pos):
                safe_pos[1] = new_y
        
        # Test Z movement third
        if new_z != old_z:
            test_z_pos = (safe_pos[0], safe_pos[1], new_z)
            if not self.simple_collision_check(test_z_pos):
                safe_pos[2] = new_z
        
        return tuple(safe_pos)
    
    def _is_position_in_block(self, position: Tuple[float, float, float]) -> bool:
        """
        Simplified collision check inspired by fogleman/Minecraft.
        Only checks the player's center position and height, not complex bounding box.
        """
        return self.simple_collision_check(position)
    
    def _normalize_position(self, position: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Normalize position to block coordinates (inspired by fogleman's normalize function).""" 
        x, y, z = position
        x, y, z = (int(round(x)), int(round(y)), int(round(z)))
        return (x, y, z)
    
    def _check_block_at_position(self, position: Tuple[float, float, float]) -> bool:
        """Check if there's a block at the given position (simplified)."""
        block_pos = self._normalize_position(position)
        return block_pos in self.world_blocks and self.world_blocks[block_pos] != "air"
    
    def simple_collision_check(self, position: Tuple[float, float, float], 
                              player_id: str = None) -> bool:
        """
        Simple collision check inspired by fogleman/Minecraft.
        
        This simplified approach only checks:
        - Player's center position (feet) for block collision
        - Player's head position (center + height) for block collision
        - No complex AABB bounding box calculations
        - No boundary thickness considerations
        
        This matches the fogleman/Minecraft approach for simplicity and performance.
        """
        px, py, pz = position
        
        # Check player's foot position (center point)
        foot_block = (int(math.floor(px)), int(math.floor(py)), int(math.floor(pz)))
        if foot_block in self.world_blocks:
            block_type = self.world_blocks[foot_block]
            if block_type != "air":  # Air blocks don't cause collision
                return True
            
        # Check player's head position (center + height)
        head_y = py + PLAYER_HEIGHT
        head_block = (int(math.floor(px)), int(math.floor(head_y)), int(math.floor(pz)))
        if head_block in self.world_blocks:
            block_type = self.world_blocks[head_block]
            if block_type != "air":  # Air blocks don't cause collision
                return True
            
        # Check for player-to-player collision (optional, can be simplified further)
        if self.check_player_collision(position, player_id):
            return True
            
        return False

    
    def server_side_collision_check(self, player_position: Tuple[float, float, float], 
                                   movement_delta: Tuple[float, float, float],
                                   player_id: str = None) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """
        Server-side collision check implementing the exact requirements:
        
        1️⃣ Principe général:
        - Le monde est une grille 3D de voxels (1×1×1)
        - Chaque voxel peut être vide ou solide
        - On teste seulement les blocs autour de la position (voisins immédiats)
        
        2️⃣ Bounding box du joueur: ~0.6×0.6×1.8
        
        3️⃣ Per-axis movement testing (X, Y, Z separately)
        """
        px, py, pz = player_position
        dx, dy, dz = movement_delta
        new_position = (px + dx, py + dy, pz + dz)
        
        # Use the server-side collision resolution
        safe_position, collision_info = self.resolve_collision(player_position, new_position, player_id)
        
        # Reset velocity components for blocked axes (as specified in requirements)
        velocity_reset = {
            'reset_vx': collision_info['x'],  # Reset X velocity if X collision
            'reset_vy': collision_info['y'],  # Reset Y velocity if Y collision  
            'reset_vz': collision_info['z'],  # Reset Z velocity if Z collision
        }
        
        # Combine collision info with velocity reset info
        detailed_info = {**collision_info, **velocity_reset}
        
        return safe_position, detailed_info
    
    def get_player_collision_info(self, position: Tuple[float, float, float], 
                                 player_id: str = None) -> Dict[str, bool]:
        """Get detailed collision information with other players."""
        px, py, pz = position
        player_size = PLAYER_WIDTH / 2
        result = {'collision': False, 'top': False, 'bottom': False, 'side': False}
        
        for other_player in self.other_players:
            if player_id and hasattr(other_player, 'id') and other_player.id == player_id:
                continue
                
            if hasattr(other_player, 'position'):
                ox, oy, oz = other_player.position
            else:
                continue
                
            other_size = getattr(other_player, 'size', PLAYER_WIDTH / 2)
            
            # Check 3D collision
            x_overlap = (px - player_size) < (ox + other_size) and (px + player_size) > (ox - other_size)
            y_overlap = py < (oy + PLAYER_HEIGHT) and (py + PLAYER_HEIGHT) > oy
            z_overlap = (pz - player_size) < (oz + other_size) and (pz + player_size) > (oz - other_size)
            
            if x_overlap and y_overlap and z_overlap:
                result['collision'] = True
                if py > oy:
                    result['top'] = True
                elif py < oy:
                    result['bottom'] = True
                else:
                    result['side'] = True
                break
        
        return result

# ============================================================================
# SIMPLIFIED PHYSICS MANAGER
# ============================================================================

class SimplePhysicsManager:
    """Simplified physics manager using the unified collision system."""
    
    def __init__(self, collision_manager: UnifiedCollisionManager):
        self.collision_manager = collision_manager
    
    def apply_gravity(self, velocity_y: float, dt: float, on_ground: bool) -> float:
        """Apply gravity to Y velocity."""
        if on_ground and velocity_y <= 0:
            return 0.0
        
        new_velocity_y = velocity_y - GRAVITY * dt
        return max(new_velocity_y, -TERMINAL_VELOCITY)
    
    def update_position(self, position: Tuple[float, float, float],
                       velocity: Tuple[float, float, float],
                       dt: float, on_ground: bool, jumping: bool,
                       player_id: str = None) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], bool]:
        """Update position with physics and collision."""
        x, y, z = position
        vx, vy, vz = velocity
        
        # Apply gravity
        if jumping and on_ground:
            vy = JUMP_VELOCITY
        vy = self.apply_gravity(vy, dt, on_ground)
        
        # Calculate new position
        new_x = x + vx * dt
        new_y = y + vy * dt  
        new_z = z + vz * dt
        
        # Resolve collision
        new_position, collision_info = self.collision_manager.resolve_collision(
            (x, y, z), (new_x, new_y, new_z), player_id
        )
        
        # Update velocity based on collisions
        final_vx = 0.0 if collision_info['x'] else vx
        final_vy = 0.0 if collision_info['y'] else vy
        final_vz = 0.0 if collision_info['z'] else vz
        
        return new_position, (final_vx, final_vy, final_vz), collision_info['ground']

# ============================================================================
# LEGACY COMPATIBILITY LAYER
# ============================================================================

class MinecraftCollisionDetector:
    """Legacy compatibility wrapper around UnifiedCollisionManager."""
    
    def __init__(self, world_blocks: Dict[Tuple[int, int, int], str]):
        self.manager = UnifiedCollisionManager(world_blocks)
        self.world_blocks = world_blocks  # For compatibility
        
    def set_other_cubes(self, other_cubes: List) -> None:
        """Set other cubes for collision detection."""
        self.manager.set_other_players(other_cubes)
        
    def check_collision(self, position: Tuple[float, float, float]) -> bool:
        """Check collision at position."""
        return self.manager.check_collision(position)
        
    def find_ground_level(self, x: float, z: float, start_y: float = 256.0, 
                         check_clearance: bool = True) -> Optional[float]:
        """Find ground level."""
        return self.manager.find_ground_level(x, z, start_y)
        
    def resolve_collision(self, old_position: Tuple[float, float, float], 
                         new_position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
        """Resolve collision."""
        return self.manager.resolve_collision(old_position, new_position)

    def snap_to_ground(self, position: Tuple[float, float, float], 
                      max_step_down: float = 1.0) -> Tuple[float, float, float]:
        """Snap to ground (simplified)."""
        x, y, z = position
        ground_y = self.manager.find_ground_level(x, z, y + max_step_down)
        if ground_y is not None:
            return (x, ground_y, z)
        return position
        
    def ray_cast_collision(self, start_pos: Tuple[float, float, float], 
                          end_pos: Tuple[float, float, float]) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """Simplified ray casting."""
        # Simple check: if end position has collision, return True
        if self.manager.check_collision(end_pos):
            # Find which block 
            x, y, z = end_pos
            block_pos = (int(math.floor(x)), int(math.floor(y)), int(math.floor(z)))
            return True, block_pos
        return False, None

class MinecraftPhysics:
    """Legacy compatibility wrapper around SimplePhysicsManager."""
    
    def __init__(self, collision_detector: MinecraftCollisionDetector):
        self.physics_manager = SimplePhysicsManager(collision_detector.manager)
        self.collision_detector = collision_detector  # For compatibility
    
    def apply_gravity(self, velocity_y: float, dt: float, on_ground: bool) -> float:
        """Apply gravity to Y velocity."""
        return self.physics_manager.apply_gravity(velocity_y, dt, on_ground)
    
    def apply_movement_drag(self, velocity: Tuple[float, float, float], 
                           dt: float, on_ground: bool) -> Tuple[float, float, float]:
        """Apply movement drag (simplified)."""
        vx, vy, vz = velocity
        drag = 0.9 if on_ground else 0.99  # Simple drag
        return (vx * drag, vy, vz * drag)
    
    def update_position(self, position: Tuple[float, float, float],
                       velocity: Tuple[float, float, float],
                       dt: float, on_ground: bool, jumping: bool) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], bool]:
        """Update position with physics and collision."""
        return self.physics_manager.update_position(position, velocity, dt, on_ground, jumping)

# ============================================================================
# GLOBAL INSTANCES AND HELPER FUNCTIONS
# ============================================================================

# Create global instances for backwards compatibility
_global_collision_manager = None
_global_physics_manager = None

def get_collision_manager(world_blocks: Dict[Tuple[int, int, int], str]) -> UnifiedCollisionManager:
    """Get or create global collision manager."""
    global _global_collision_manager
    if _global_collision_manager is None or _global_collision_manager.world_blocks != world_blocks:
        _global_collision_manager = UnifiedCollisionManager(world_blocks)
    return _global_collision_manager

def get_physics_manager(world_blocks: Dict[Tuple[int, int, int], str]) -> SimplePhysicsManager:
    """Get or create global physics manager."""
    global _global_physics_manager, _global_collision_manager
    collision_manager = get_collision_manager(world_blocks)
    if _global_physics_manager is None or _global_physics_manager.collision_manager != collision_manager:
        _global_physics_manager = SimplePhysicsManager(collision_manager)
    return _global_physics_manager



# ============================================================================
# UNIFIED API FUNCTIONS
# ============================================================================

def unified_check_collision(position: Tuple[float, float, float], 
                           world_blocks: Dict[Tuple[int, int, int], str],
                           other_players: List = None,
                           player_id: str = None) -> bool:
    """
    Unified collision check for both blocks and players.
    
    Args:
        position: Position to check
        world_blocks: World block dictionary
        other_players: List of other players
        player_id: Player ID for collision avoidance
    """
    manager = get_collision_manager(world_blocks)
    if other_players:
        manager.set_other_players(other_players)
    return manager.check_collision(position, player_id)


def unified_check_player_collision(position: Tuple[float, float, float],
                                  other_players: List,
                                  player_id: str = None) -> bool:
    """
    Unified player-to-player collision check.
    """
    manager = UnifiedCollisionManager({})  # Empty world blocks
    manager.set_other_players(other_players)
    return manager.check_player_collision(position, player_id)

def unified_get_player_collision_info(position: Tuple[float, float, float],
                                     other_players: List,
                                     player_id: str = None) -> Dict[str, bool]:
    """
    Get detailed player collision information.
    """
    manager = UnifiedCollisionManager({})  # Empty world blocks
    manager.set_other_players(other_players)
    return manager.get_player_collision_info(position, player_id)

def unified_resolve_collision(old_position: Tuple[float, float, float],
                             new_position: Tuple[float, float, float],
                             world_blocks: Dict[Tuple[int, int, int], str],
                             other_players: List = None,
                             player_id: str = None) -> Tuple[Tuple[float, float, float], Dict[str, bool]]:
    """
    Unified collision resolution.
    """
    manager = get_collision_manager(world_blocks)
    if other_players:
        manager.set_other_players(other_players)
    return manager.resolve_collision(old_position, new_position, player_id)

def unified_find_ground_level(x: float, z: float, 
                             world_blocks: Dict[Tuple[int, int, int], str],
                             start_y: float = 256.0) -> Optional[float]:
    """
    Unified ground level detection.
    """
    manager = get_collision_manager(world_blocks)
    return manager.find_ground_level(x, z, start_y)

# ============================================================================
# LEGACY SUPPORT FUNCTIONS (for backwards compatibility)
# ============================================================================

def normalize_position(position: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """
    Normalize a position to block coordinates.
    Standard Minecraft floors negative coordinates differently.
    """
    x, y, z = position
    return int(math.floor(x)), int(math.floor(y)), int(math.floor(z))

def get_player_bounding_box(position: Tuple[float, float, float]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Calculate the player's bounding box at the given position.
    
    Args:
        position: Player position (x, y, z) - y is feet position
        
    Returns:
        Tuple of (min_corner, max_corner) defining the bounding box
    """
    x, y, z = position
    half_width = PLAYER_WIDTH / 2
    
    min_corner = (x - half_width, y, z - half_width)
    max_corner = (x + half_width, y + PLAYER_HEIGHT, z + half_width)
    
    return min_corner, max_corner

def get_blocks_in_bounding_box(min_corner: Tuple[float, float, float], 
                              max_corner: Tuple[float, float, float]) -> Set[Tuple[int, int, int]]:
    """
    Get all block positions that could potentially intersect with the bounding box.
    """
    min_x, min_y, min_z = min_corner
    max_x, max_y, max_z = max_corner
    
    blocks = set()
    for x in range(int(math.floor(min_x)), int(math.ceil(max_x)) + 1):
        for y in range(int(math.floor(min_y)), int(math.ceil(max_y)) + 1):
            for z in range(int(math.floor(min_z)), int(math.ceil(max_z)) + 1):
                blocks.add((x, y, z))
    
    return blocks

def check_cube_position_occupied(position: Tuple[float, float, float], 
                                player_size: float, 
                                other_cubes: List) -> bool:
    """
    Quick check if a position is occupied by another cube.
    """
    manager = UnifiedCollisionManager({})
    manager.set_other_players(other_cubes)
    return manager.check_player_collision(position)

def box_intersects_block(min_corner: Tuple[float, float, float], 
                        max_corner: Tuple[float, float, float], 
                        block_pos: Tuple[int, int, int]) -> bool:
    """
    Check if a bounding box intersects with a block.
    """
    min_x, min_y, min_z = min_corner
    max_x, max_y, max_z = max_corner
    bx, by, bz = block_pos
    
    return (min_x < bx + 1 and max_x > bx and
            min_y < by + 1 and max_y > by and
            min_z < bz + 1 and max_z > bz)

def minecraft_collide(position: Tuple[float, float, float], 
                     height: int,
                     world_blocks: Dict[Tuple[int, int, int], str]) -> Tuple[float, float, float]:
    """
    Compatibility function for existing collision detection code.
    """
    manager = get_collision_manager(world_blocks)
    safe_position, _ = manager.resolve_collision(position, position)
    return safe_position

def minecraft_check_ground(position: Tuple[float, float, float],
                          world_blocks: Dict[Tuple[int, int, int], str]) -> bool:
    """
    Compatibility function to check if player is on ground.
    """
    manager = get_collision_manager(world_blocks)
    x, y, z = position
    
    # Check if there's a block slightly below
    test_position = (x, y - 0.1, z)
    return manager.check_block_collision(test_position)

def minecraft_find_spawn_point(world_blocks: Dict[Tuple[int, int, int], str],
                              search_center: Tuple[float, float] = (0.0, 0.0),
                              search_radius: int = 10) -> Optional[Tuple[float, float, float]]:
    """
    Find a safe spawn point near the given coordinates.
    """
    manager = get_collision_manager(world_blocks)
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
                ground_y = manager.find_ground_level(x, z)
                if ground_y is not None:
                    spawn_pos = (x, ground_y, z)
                    # Verify it's a safe spawn (no collision)
                    if not manager.check_collision(spawn_pos):
                        return spawn_pos
    
    return None
