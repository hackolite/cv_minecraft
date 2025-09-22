#!/usr/bin/env python3
"""
Unified Minecraft Physics System
================================

This module implements a unified, simplified Minecraft-style physics system 
that consolidates all collision detection into a single, clean interface.
Used by both client and server for consistent behavior.

COLLISION SYSTEM APPROACH:
=========================
The collision detection system has been simplified and is inspired by the
fogleman/Minecraft implementation (https://github.com/fogleman/Minecraft/blob/master/main.py#L596-L679).

This simple approach:
- Tests only the player's central position and height (no complex bounding box)
- Backs up the player on collision by adjusting position on the affected axis  
- Blocks falling/rising if collision with ground/ceiling
- Uses simple collision logic without sweeping AABB or complex per-axis resolution
- Eliminates diagonal tunneling prevention for simplicity
- Provides better performance through simplified calculations

Key Features:
- Unified collision management in a single module
- Simplified algorithms without over-engineering  
- Clean interfaces for both client and server
- Elimination of code duplication
- Standard Minecraft physics constants
- Simple collision detection inspired by fogleman/Minecraft
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
        Check collision with world blocks using robust AABB collision detection.
        
        Player is a 1x1x1 cube with dimensions:
        - Width (X): 1.0 (±0.5 from center)
        - Height (Y): 1.0 (from feet to head) 
        - Depth (Z): 1.0 (±0.5 from center)
        """
        px, py, pz = position
        
        # Player dimensions (1x1x1 cube)
        half_width = PLAYER_WIDTH / 2    # 0.5
        height = PLAYER_HEIGHT           # 1.0
        half_depth = PLAYER_WIDTH / 2    # 0.5
        
        # Player bounding box - calculate range without epsilon to avoid missing blocks
        player_min_x = px - half_width
        player_max_x_range = px + half_width  # For range calculation without epsilon
        player_min_y = py               # Y is feet position
        player_max_y_range = py + height      # For range calculation without epsilon
        player_min_z = pz - half_depth
        player_max_z_range = pz + half_depth  # For range calculation without epsilon
        
        # Player bounding box for AABB test - with epsilon to prevent floating point issues
        player_max_x = px + half_width - COLLISION_EPSILON
        player_max_y = py + height      # Head position
        player_max_z = pz + half_depth - COLLISION_EPSILON
        
        # Calculate which blocks might intersect with player bounding box
        # Use coordinates without epsilon to ensure we don't miss adjacent blocks
        xmin = int(math.floor(player_min_x))
        xmax = int(math.floor(player_max_x_range))
        ymin = int(math.floor(player_min_y))
        ymax = int(math.floor(player_max_y_range))
        zmin = int(math.floor(player_min_z))
        zmax = int(math.floor(player_max_z_range))
        
        # Test blocks in the calculated range
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                for z in range(zmin, zmax + 1):
                    if (x, y, z) in self.world_blocks:
                        block_type = self.world_blocks[(x, y, z)]
                        
                        # AIR blocks should not cause collision - players can pass through
                        if block_type == "air":
                            continue
                        
                        # Block boundaries (1x1x1 voxel from x,y,z to x+1,y+1,z+1)
                        block_min_x, block_max_x = float(x), float(x + 1)
                        block_min_y, block_max_y = float(y), float(y + 1)
                        block_min_z, block_max_z = float(z), float(z + 1)
                        
                        # AABB intersection test - robust face collision detection with boundary contact detection
                        # Use the range coordinates (without epsilon) for the actual intersection test
                        # to ensure we detect boundary contact properly
                        player_max_x_test = px + half_width         # Without epsilon for boundary detection
                        player_max_y_test = py + height             # Without epsilon for boundary detection
                        player_max_z_test = pz + half_depth         # Without epsilon for boundary detection
                        
                        # Use < and >= for proper boundary collision detection (>= to catch exact boundary contact)
                        if (player_min_x < block_max_x and player_max_x_test >= block_min_x and
                            player_min_y < block_max_y and player_max_y_test >= block_min_y and
                            player_min_z < block_max_z and player_max_z_test >= block_min_z):
                            
                            # Log collision for debugging
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            collision_logger.debug(f"🚫 COLLISION DÉTECTÉE - Bloc")
                            collision_logger.debug(f"   Position joueur: ({px:.3f}, {py:.3f}, {pz:.3f})")
                            collision_logger.debug(f"   Position bloc: ({x}, {y}, {z}) type: {block_type}")
                            collision_logger.debug(f"   AABB Joueur: ({player_min_x:.3f},{player_min_y:.3f},{player_min_z:.3f}) to ({player_max_x:.3f},{player_max_y:.3f},{player_max_z:.3f})")
                            collision_logger.debug(f"   AABB Bloc: ({block_min_x:.1f},{block_min_y:.1f},{block_min_z:.1f}) to ({block_max_x:.1f},{block_max_y:.1f},{block_max_z:.1f})")
                            
                            return True
        return False


    
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
        Simple, effective collision resolution to prevent cube face traversal.
        
        This method prevents both direct collision and diagonal traversal by:
        1. Checking if the starting position is already in a block and snapping out if needed
        2. Checking if the direct path would go through any blocks
        3. If so, using axis-by-axis movement that prevents traversal
        4. Ensuring the final position is safe and reachable without traversal
        """
        collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        
        # CRITICAL FIX: Check if starting position is already in a block
        # This prevents the player from being stuck inside blocks
        if self._is_position_in_block(old_pos):
            # Player is already inside a block - snap them to nearest safe position
            safe_start_pos = self._snap_out_of_block(old_pos, player_id or "player", 0.01)
            # Use the snapped position as the new starting point
            old_pos = safe_start_pos
            # Mark collision on all axes since we had to snap
            collision_info['x'] = True
            collision_info['z'] = True
        
        # Check if new position would put player inside a block
        if self._is_position_in_block(new_pos):
            # Player would be inside a block - find safe position
            safe_pos = self._find_safe_position_axis_by_axis(old_pos, new_pos)
            
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
            # Target position is safe, but check for traversal along the path
            if self._path_intersects_blocks(old_pos, new_pos):
                # Path goes through blocks - use safe axis-by-axis movement with traversal check
                safe_pos = self._find_safe_position_with_traversal_check(old_pos, new_pos)
                
                # Mark axes as collided if movement was restricted
                old_x, old_y, old_z = old_pos
                safe_x, safe_y, safe_z = safe_pos
                
                if abs(safe_x - old_x) < abs(new_pos[0] - old_x):
                    collision_info['x'] = True
                if abs(safe_y - old_y) < abs(new_pos[1] - old_y):
                    collision_info['y'] = True
                if abs(safe_z - old_z) < abs(new_pos[2] - old_z):
                    collision_info['z'] = True
            else:
                # No collision and no traversal, allow movement
                safe_pos = new_pos
        
        # Check if on ground
        ground_test_pos = (safe_pos[0], safe_pos[1] - 0.1, safe_pos[2])
        if self._is_position_in_block(ground_test_pos):
            collision_info['ground'] = True
        
        return safe_pos, collision_info
    
    def _find_safe_position_axis_by_axis(self, old_pos: Tuple[float, float, float], 
                                        new_pos: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Find safe position using simple axis-by-axis movement (original behavior).
        This is used when the target position is inside a block.
        """
        old_x, old_y, old_z = old_pos
        new_x, new_y, new_z = new_pos
        
        # Start with old position
        safe_pos = list(old_pos)
        
        # Test X movement only (if different)
        if new_x != old_x:
            test_x_pos = (new_x, safe_pos[1], safe_pos[2])
            if not self._is_position_in_block(test_x_pos):
                safe_pos[0] = new_x
        
        # Test Y movement only (if different)  
        if new_y != old_y:
            test_y_pos = (safe_pos[0], new_y, safe_pos[2])
            if not self._is_position_in_block(test_y_pos):
                safe_pos[1] = new_y
        
        # Test Z movement only (if different)
        if new_z != old_z:
            test_z_pos = (safe_pos[0], safe_pos[1], new_z)
            if not self._is_position_in_block(test_z_pos):
                safe_pos[2] = new_z
        
        return tuple(safe_pos)
    
    def _path_intersects_blocks(self, start_pos: Tuple[float, float, float], 
                               end_pos: Tuple[float, float, float]) -> bool:
        """
        Check if the direct path from start to end intersects any blocks.
        This prevents diagonal traversal through blocks.
        """
        # Sample points along the path to check for intersections
        samples = 16  # Higher sample count for more accuracy
        
        for i in range(1, samples):  # Skip start point (i=0)
            t = i / samples
            sample_x = start_pos[0] + t * (end_pos[0] - start_pos[0])
            sample_y = start_pos[1] + t * (end_pos[1] - start_pos[1])
            sample_z = start_pos[2] + t * (end_pos[2] - start_pos[2])
            sample_pos = (sample_x, sample_y, sample_z)
            
            if self._is_position_in_block(sample_pos):
                return True
        
        return False
    
    def _find_safe_position_with_traversal_check(self, old_pos: Tuple[float, float, float], 
                                                new_pos: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Find safe position with traversal prevention.
        
        This method ensures that:
        1. Movement is tried axis by axis
        2. Each intermediate position is safe
        3. No traversal through blocks occurs
        4. The overall movement doesn't allow diagonal traversal
        """
        old_x, old_y, old_z = old_pos
        new_x, new_y, new_z = new_pos
        
        # Start with old position
        safe_pos = list(old_pos)
        
        # Test X movement only (if different)
        if new_x != old_x:
            test_x_pos = (new_x, safe_pos[1], safe_pos[2])
            # Check both that position is safe AND path to it is clear
            if (not self._is_position_in_block(test_x_pos) and 
                not self._path_intersects_blocks((safe_pos[0], safe_pos[1], safe_pos[2]), test_x_pos)):
                safe_pos[0] = new_x
        
        # Test Y movement only (if different)  
        if new_y != old_y:
            test_y_pos = (safe_pos[0], new_y, safe_pos[2])
            # Check both that position is safe AND path to it is clear
            if (not self._is_position_in_block(test_y_pos) and 
                not self._path_intersects_blocks((safe_pos[0], safe_pos[1], safe_pos[2]), test_y_pos)):
                safe_pos[1] = new_y
        
        # Test Z movement only (if different)
        if new_z != old_z:
            test_z_pos = (safe_pos[0], safe_pos[1], new_z)
            # Check both that position is safe AND path to it is clear
            if (not self._is_position_in_block(test_z_pos) and 
                not self._path_intersects_blocks((safe_pos[0], safe_pos[1], safe_pos[2]), test_z_pos)):
                safe_pos[2] = new_z
        
        # CRITICAL FIX: Check that the final movement from old_pos to safe_pos doesn't traverse
        # This prevents cases where axis-by-axis movement is safe but overall path traverses
        final_pos = tuple(safe_pos)
        if self._path_intersects_blocks(old_pos, final_pos):
            # If the overall path would traverse, don't allow any movement
            return old_pos
        
        # Final verification that the position is safe
        if self._is_position_in_block(final_pos):
            # If the final position is not safe, revert to old position
            return old_pos
        
        return final_pos
    
    def _is_position_in_block(self, position: Tuple[float, float, float]) -> bool:
        """Check if position is inside any block (proper AABB collision detection).""" 
        # Original AABB implementation
        px, py, pz = position
        
        # Use proper player bounding box for accurate collision detection
        player_half_width = PLAYER_WIDTH / 2  # 0.5 - proper player dimensions
        
        # Player bounding box - calculate range without epsilon to avoid missing blocks
        player_min_x = px - player_half_width
        player_max_x_range = px + player_half_width  # For range calculation without epsilon
        player_min_y = py               # Y is feet position
        player_max_y_range = py + PLAYER_HEIGHT      # For range calculation without epsilon
        player_min_z = pz - player_half_width
        player_max_z_range = pz + player_half_width  # For range calculation without epsilon
        
        # Player bounding box for AABB test - with epsilon to prevent floating point issues
        player_max_x = px + player_half_width - COLLISION_EPSILON
        player_max_y = py + PLAYER_HEIGHT
        player_max_z = pz + player_half_width - COLLISION_EPSILON
        
        # Calculate which blocks might intersect with player bounding box
        # Use coordinates without epsilon to ensure we don't miss adjacent blocks
        xmin = int(math.floor(player_min_x))
        xmax = int(math.floor(player_max_x_range))
        ymin = int(math.floor(player_min_y))
        ymax = int(math.floor(player_max_y_range))
        zmin = int(math.floor(player_min_z))
        zmax = int(math.floor(player_max_z_range))
        
        # Test blocks in the calculated range
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                for z in range(zmin, zmax + 1):
                    if (x, y, z) in self.world_blocks:
                        block_type = self.world_blocks[(x, y, z)]
                        
                        # AIR blocks should not cause collision - players can pass through
                        if block_type == "air":
                            continue
                        
                        # Block boundaries (1x1x1 voxel from x,y,z to x+1,y+1,z+1)
                        block_min_x, block_max_x = float(x), float(x + 1)
                        block_min_y, block_max_y = float(y), float(y + 1)
                        block_min_z, block_max_z = float(z), float(z + 1)
                        
                        # AABB intersection test - proper collision detection with boundary contact detection
                        # Use the range coordinates (without epsilon) for the actual intersection test
                        # to ensure we detect boundary contact properly
                        player_max_x_test = px + player_half_width  # Without epsilon for boundary detection
                        player_max_y_test = py + PLAYER_HEIGHT      # Without epsilon for boundary detection  
                        player_max_z_test = pz + player_half_width  # Without epsilon for boundary detection
                        
                        # Use < and >= for proper boundary collision detection (>= to catch exact boundary contact)
                        if (player_min_x < block_max_x and player_max_x_test >= block_min_x and
                            player_min_y < block_max_y and player_max_y_test >= block_min_y and
                            player_min_z < block_max_z and player_max_z_test >= block_min_z):
                            return True
        
        return False
    

    def _normalize_position(self, position: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Normalize position to block coordinates (like fogleman's normalize function).""" 
        x, y, z = position
        x, y, z = (int(round(x)), int(round(y)), int(round(z)))
        return (x, y, z)
    
    def _check_block_at_position(self, position: Tuple[float, float, float]) -> bool:
        """Check if there's a block at the given position."""
        block_pos = self._normalize_position(position)
        return block_pos in self.world_blocks
    
    def _snap_out_of_block(self, pos: Tuple[float, float, float], 
                          player_id: str, clearance: float) -> Tuple[float, float, float]:
        """Snap player out of block ensuring minimum clearance from all block faces."""
        px, py, pz = pos
        player_half_width = PLAYER_WIDTH / 2
        
        # Find all blocks that the player is currently intersecting
        player_min_x = px - player_half_width
        player_max_x = px + player_half_width
        player_min_y = py
        player_max_y = py + PLAYER_HEIGHT
        player_min_z = pz - player_half_width
        player_max_z = pz + player_half_width
        
        # Find intersecting blocks
        xmin = int(math.floor(player_min_x))
        xmax = int(math.floor(player_max_x))
        ymin = int(math.floor(player_min_y))
        ymax = int(math.floor(player_max_y))
        zmin = int(math.floor(player_min_z))
        zmax = int(math.floor(player_max_z))
        
        # For simplicity, focus on the primary intersecting block
        # In most cases, the player will be intersecting with just one block
        intersecting_blocks = []
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                for z in range(zmin, zmax + 1):
                    if (x, y, z) in self.world_blocks and self.world_blocks[(x, y, z)] != "air":
                        intersecting_blocks.append((x, y, z))
        
        if not intersecting_blocks:
            return pos  # No intersecting blocks found
        
        # Use the first intersecting block (most common case)
        block_x, block_y, block_z = intersecting_blocks[0]
        block_min_x, block_max_x = float(block_x), float(block_x + 1)
        block_min_y, block_max_y = float(block_y), float(block_y + 1)
        block_min_z, block_max_z = float(block_z), float(block_z + 1)
        
        # Calculate candidates that ensure COMPLETE separation with clearance
        candidates = [
            # Move completely left of block
            (block_min_x - player_half_width - clearance, py, pz),
            # Move completely right of block
            (block_max_x + player_half_width + clearance, py, pz),
            # Move completely below block
            (px, block_min_y - PLAYER_HEIGHT - clearance, pz),
            # Move completely above block
            (px, block_max_y + clearance, pz),
            # Move completely in front of block
            (px, py, block_min_z - player_half_width - clearance),
            # Move completely behind block
            (px, py, block_max_z + player_half_width + clearance),
        ]
        
        # Find the candidate with minimum displacement that has no collision
        best_candidate = None
        min_distance = float('inf')
        
        for candidate in candidates:
            if not self.check_collision(candidate, player_id):
                # Calculate distance from original position
                distance = math.sqrt((candidate[0] - px)**2 + (candidate[1] - py)**2 + (candidate[2] - pz)**2)
                if distance < min_distance:
                    min_distance = distance
                    best_candidate = candidate
        
        if best_candidate:
            return best_candidate
        
        # Fallback: move far away in the safest direction
        fallback_positions = [
            (px - 3.0, py, pz),    # Far left
            (px + 3.0, py, pz),    # Far right
            (px, py + 3.0, pz),    # Far up
            (px, py, pz - 3.0),    # Far back
            (px, py, pz + 3.0),    # Far forward
        ]
        
        for fallback in fallback_positions:
            if not self.check_collision(fallback, player_id):
                return fallback
        
        return pos  # Last resort


    def _snap_to_safe_x_position(self, old_x: float, new_x: float, y: float, z: float, player_id: str, clearance: float) -> float:
          player_half_width = PLAYER_WIDTH / 2
          block_y = int(math.floor(y))
          block_z = int(math.floor(z))
          safe_x = new_x  # Default to intended position
      
          if new_x > old_x:  # Moving right
              for block_x in range(int(math.floor(old_x)), int(math.floor(new_x)) + 2):
                  if (block_x, block_y, block_z) in self.world_blocks:
                      block_type = self.world_blocks[(block_x, block_y, block_z)]
                      if block_type != "air":
                          safe_x = float(block_x) - player_half_width - clearance
                          safe_x = max(safe_x, old_x)
                          break
          else:  # Moving left
              for block_x in range(int(math.floor(new_x)), int(math.floor(old_x)) + 2):
                  if (block_x, block_y, block_z) in self.world_blocks:
                      block_type = self.world_blocks[(block_x, block_y, block_z)]
                      if block_type != "air":
                          safe_x = float(block_x + 1) + player_half_width + clearance
                          safe_x = min(safe_x, old_x)
                          break
      
          # Collision check: if still inside a block, fallback to previous position
          if self.check_collision((safe_x, y, z), player_id):
              return old_x
          return safe_x

    def _snap_to_safe_z_position(self, x: float, old_z: float, new_z: float, y: float, player_id: str, clearance: float) -> float:
              player_half_width = PLAYER_WIDTH / 2
              block_x = int(math.floor(x))
              block_y = int(math.floor(y))
              safe_z = new_z  # Default to intended position
          
              if new_z > old_z:  # Moving forward
                  for block_z in range(int(math.floor(old_z)), int(math.floor(new_z)) + 2):
                      if (block_x, block_y, block_z) in self.world_blocks:
                          block_type = self.world_blocks[(block_x, block_y, block_z)]
                          if block_type != "air":
                              safe_z = float(block_z) - player_half_width - clearance
                              safe_z = max(safe_z, old_z)
                              break
              else:  # Moving backward
                  for block_z in range(int(math.floor(new_z)), int(math.floor(old_z)) + 2):
                      if (block_x, block_y, block_z) in self.world_blocks:
                          block_type = self.world_blocks[(block_x, block_y, block_z)]
                          if block_type != "air":
                              safe_z = float(block_z + 1) + player_half_width + clearance
                              safe_z = min(safe_z, old_z)
                              break
          
              # Collision check: if still inside a block, fallback to previous position
              if self.check_collision((x, y, safe_z), player_id):
                  return old_z
              return safe_z
  

    
    def _snap_to_safe_y_position(self, x: float, z: float, old_y: float, new_y: float, 
                                player_id: str, clearance: float) -> float:
        """Snap to safe Y position with minimum clearance from block faces."""
        # Find blocks that could cause collision in the Y direction
        
        # Get the X and Z block coordinates where collision would occur
        block_x = int(math.floor(x))
        block_z = int(math.floor(z))
        
        # Check if we're moving up or down
        if new_y > old_y:  # Moving up
            # Find the first block that would cause collision with player's head
            for block_y in range(int(math.floor(old_y)), int(math.floor(new_y + PLAYER_HEIGHT)) + 2):
                if (block_x, block_y, block_z) in self.world_blocks:
                    block_type = self.world_blocks[(block_x, block_y, block_z)]
                    if block_type != "air":
                        # Snap player feet to below this block with clearance
                        safe_y = float(block_y) - PLAYER_HEIGHT - clearance
                        return max(safe_y, old_y)  # Don't go backwards
        else:  # Moving down
            # Find the first block that would cause collision with player's feet
            for block_y in range(int(math.floor(new_y)), int(math.floor(old_y)) + 2):
                if (block_x, block_y, block_z) in self.world_blocks:
                    block_type = self.world_blocks[(block_x, block_y, block_z)]
                    if block_type != "air":
                        # Snap player feet to on top of this block with clearance
                        safe_y = float(block_y + 1) + clearance
                        return min(safe_y, old_y)  # Don't go backwards
        
        return old_y  # No blocking block found
    
    def simple_collision_check(self, position: Tuple[float, float, float], 
                              player_id: str = None) -> bool:
        """
        Simple collision check inspired by fogleman/Minecraft.
        Only checks the player's center position and height, not a complex bounding box.
        
        This is much simpler than the complex AABB collision detection.
        """
        px, py, pz = position
        
        # Simple approach: check if the player's feet and head positions collide with blocks
        # Check player's foot position (center)
        foot_block = (int(math.floor(px)), int(math.floor(py)), int(math.floor(pz)))
        if foot_block in self.world_blocks:
            return True
            
        # Check player's head position (center + height)
        head_y = py + PLAYER_HEIGHT
        head_block = (int(math.floor(px)), int(math.floor(head_y)), int(math.floor(pz)))
        if head_block in self.world_blocks:
            return True
            
        # Check for player-to-player collision (simplified)
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
    max_corner = (x + half_width - COLLISION_EPSILON, y + PLAYER_HEIGHT, z + half_width - COLLISION_EPSILON)
    
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
