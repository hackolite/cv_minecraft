#!/usr/bin/env python3
"""
Unified Minecraft Physics System
================================

This module implements a unified, simplified Minecraft-style physics system 
that consolidates all collision detection into a single, clean interface.
Used by both client and server for consistent behavior.

Key Features:
- Unified collision management in a single module
- Simplified algorithms without over-engineering  
- Clean interfaces for both client and server
- Elimination of code duplication
- Standard Minecraft physics constants
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
        Check collision with world blocks using server-side voxel collision detection.
        
        Implements the exact formulas specified:
        - xmin = floor(px - largeur/2)
        - xmax = floor(px + largeur/2) 
        - ymin = floor(py)
        - ymax = floor(py + hauteur)
        - zmin = floor(pz - profondeur/2)
        - zmax = floor(pz + profondeur/2)
        """
        px, py, pz = position
        largeur = PLAYER_WIDTH      # 0.6
        hauteur = PLAYER_HEIGHT     # 1.8
        profondeur = PLAYER_WIDTH   # 0.6 (same as width for square base)
        
        # Calculate voxel bounds using exact formulas from problem statement
        xmin = int(math.floor(px - largeur / 2))
        xmax = int(math.floor(px + largeur / 2))
        ymin = int(math.floor(py))
        ymax = int(math.floor(py + hauteur))
        zmin = int(math.floor(pz - profondeur / 2))
        zmax = int(math.floor(pz + profondeur / 2))
        
        # Test only the voxels in the calculated range (neighboring voxels)
        # This avoids testing the entire world - only relevant blocks
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                for z in range(zmin, zmax + 1):
                    if (x, y, z) in self.world_blocks:
                        # Voxel exists at this position - check AABB intersection
                        # Player bounding box vs voxel (1x1x1 block)
                        player_min_x = px - largeur / 2
                        player_max_x = px + largeur / 2
                        player_min_y = py
                        player_max_y = py + hauteur
                        player_min_z = pz - profondeur / 2
                        player_max_z = pz + profondeur / 2
                        
                        # Block boundaries (voxel from x,y,z to x+1,y+1,z+1)
                        block_min_x, block_max_x = float(x), float(x + 1)
                        block_min_y, block_max_y = float(y), float(y + 1)
                        block_min_z, block_max_z = float(z), float(z + 1)
                        
                        # AABB intersection test
                        if (player_min_x < block_max_x and player_max_x > block_min_x and
                            player_min_y < block_max_y and player_max_y > block_min_y and
                            player_min_z < block_max_z and player_max_z > block_min_z):
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
                return True
        return False
    
    def check_collision(self, position: Tuple[float, float, float], player_id: str = None) -> bool:
        """Check both block and player collisions."""
        return (self.check_block_collision(position) or 
                self.check_player_collision(position, player_id))
    
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
            Collision resolution améliorée pour éviter de traverser les coins.
            Test Y en premier, puis X et Z avec marge epsilon.
            """
            collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
            final_pos = list(old_pos)
            
            # Appliquer un petit epsilon pour éviter de passer à travers les coins
            epsilon = 0.001
            
            # 1️⃣ Test axe Y (vertical)
            test_pos_y = (old_pos[0], new_pos[1], old_pos[2])
            if not self.check_collision(test_pos_y, player_id):
                final_pos[1] = new_pos[1]
            else:
                collision_info['y'] = True
                # Si chute, ajuster au sol
                if new_pos[1] < old_pos[1]:
                    ground_level = self.find_ground_level(final_pos[0], final_pos[2], old_pos[1])
                    if ground_level is not None:
                        final_pos[1] = ground_level
            
            # 2️⃣ Test axe X (horizontal) avec marge
            test_pos_x = (new_pos[0] + (epsilon if new_pos[0] > final_pos[0] else -epsilon),
                          final_pos[1], final_pos[2])
            if not self.check_collision(test_pos_x, player_id):
                final_pos[0] = new_pos[0]
            else:
                collision_info['x'] = True
            
            # 3️⃣ Test axe Z (horizontal) avec marge
            test_pos_z = (final_pos[0], final_pos[1], new_pos[2] + (epsilon if new_pos[2] > final_pos[2] else -epsilon))
            if not self.check_collision(test_pos_z, player_id):
                final_pos[2] = new_pos[2]
            else:
                collision_info['z'] = True
            
            # Vérifier le sol
            ground_test = (final_pos[0], final_pos[1] - 0.1, final_pos[2])
            collision_info['ground'] = self.check_block_collision(ground_test)
            
            return tuple(final_pos), collision_info

    
    
    
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
# TICK-BASED PHYSICS MANAGER (IA-FRIENDLY VERSION)
# ============================================================================

class TickBasedPhysicsManager:
    """
    Physics manager implementing tick-based movement with sub-steps as specified.
    
    🔹 Logique de la collision (version IA-friendly)
    
    1. Représentation:
    - Monde = grille 3D où chaque cellule peut être vide ou solide
    - Joueur = boîte rectangulaire verticale (AABB)
    - Vitesse du joueur = (vx, vy, vz) mise à jour à chaque tick
    - Paramètres: gravité, vitesse terminale, pad (tolérance)
    
    2. Mise à jour par tick:
    - Appliquer la gravité: vy = vy - gravité * dt
    - Limiter la vitesse terminale: vy = max(vy, -vitesse_terminale)
    - Calculer translation: dx = vx * dt, dy = vy * dt, dz = vz * dt
    - Diviser en sous-étapes pour éviter tunneling
    
    3. Déplacement et collisions:
    - Position candidate = (x+dx, y+dy, z+dz)
    - Correction par axe (X, Y, Z indépendamment)
    - Si collision → repositionner et mettre vitesse = 0 sur cet axe
    """
    
    def __init__(self, collision_manager: UnifiedCollisionManager):
        self.collision_manager = collision_manager
        self.gravity = GRAVITY                    # gravité
        self.terminal_velocity = TERMINAL_VELOCITY # vitesse_terminale
        self.sub_steps = 8                       # nombre_etapes pour éviter tunneling
        
    def apply_gravity_tick(self, velocity_y: float, dt: float) -> float:
        """
        Appliquer la gravité selon la spécification:
        vy = vy - gravité * dt
        vy = max(vy, -vitesse_terminale)
        """
        # Appliquer la gravité
        vy = velocity_y - self.gravity * dt
        
        # Appliquer la vitesse terminale
        vy = max(vy, -self.terminal_velocity)
        
        return vy
    
    def apply_movement_substep(self, position: Tuple[float, float, float], 
                              velocity: Tuple[float, float, float],
                              dt_substep: float,
                              player_id: str = None) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        Appliquer un déplacement en sous-étape avec collision.
        
        Pour chaque sous-étape:
        - Position candidate = (x+dx, y+dy, z+dz)
        - Vérifier collisions avec les blocs voisins
        - Corriger par axe et remettre vitesse = 0 si collision
        """
        x, y, z = position
        vx, vy, vz = velocity
        
        # Calculer la translation souhaitée pour cette sous-étape
        dx = vx * dt_substep
        dy = vy * dt_substep  
        dz = vz * dt_substep
        
        # Position candidate
        new_position = (x + dx, y + dy, z + dz)
        
        # Résolution des collisions par axe avec le système existant
        safe_position, collision_info = self.collision_manager.resolve_collision(
            position, new_position, player_id
        )
        
        # Corriger la vitesse selon les collisions détectées
        # Si collision → replacer position au bord du bloc, mettre vitesse = 0
        final_vx = 0.0 if collision_info['x'] else vx
        final_vy = 0.0 if collision_info['y'] else vy  
        final_vz = 0.0 if collision_info['z'] else vz
        
        return safe_position, (final_vx, final_vy, final_vz)
    
    def update_tick(self, position: Tuple[float, float, float],
                   velocity: Tuple[float, float, float], 
                   dt: float,
                   jumping: bool = False,
                   player_id: str = None) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], Dict[str, bool]]:
        """
        Mise à jour complète par tick selon la spécification.
        
        À chaque tick (ex. toutes les 16 ms):
        1. Appliquer la gravité
        2. Calculer la translation souhaitée  
        3. Diviser le déplacement en sous-étapes
        4. Pour chaque sous-étape: appliquer_deplacement()
        
        Retourne: (nouvelle_position, nouvelle_vitesse, info_collision)
        """
        x, y, z = position
        vx, vy, vz = velocity
        
        # Gestion du saut
        if jumping:
            # Vérifier si le joueur est au sol
            ground_test = (x, y - 0.1, z)
            on_ground = self.collision_manager.check_block_collision(ground_test)
            if on_ground:
                vy = JUMP_VELOCITY
        
        # 1. Appliquer la gravité
        vy = self.apply_gravity_tick(vy, dt)
        
        # Position et vitesse actuelles pour les sous-étapes
        current_position = (x, y, z)
        current_velocity = (vx, vy, vz)
        
        # 2. Diviser le déplacement en sous-étapes pour éviter le tunneling
        dt_substep = dt / self.sub_steps
        
        # Information sur les collisions détectées
        final_collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
        
        # 3. Pour chaque sous-étape: appliquer_deplacement()
        for step in range(self.sub_steps):
            old_velocity = current_velocity
            current_position, current_velocity = self.apply_movement_substep(
                current_position, current_velocity, dt_substep, player_id
            )
            
            # Accumuler les informations de collision
            # Si la vitesse a été réinitialisée, cela indique une collision
            if current_velocity[0] == 0.0 and old_velocity[0] != 0.0:
                final_collision_info['x'] = True
            if current_velocity[1] == 0.0 and old_velocity[1] != 0.0:
                final_collision_info['y'] = True  
            if current_velocity[2] == 0.0 and old_velocity[2] != 0.0:
                final_collision_info['z'] = True
                
            # Si une collision est détectée sur un axe, arrêter le mouvement sur cet axe
            # pour toutes les sous-étapes restantes
            if final_collision_info['x']:
                current_velocity = (0.0, current_velocity[1], current_velocity[2])
            if final_collision_info['y']:
                current_velocity = (current_velocity[0], 0.0, current_velocity[2])
            if final_collision_info['z']:
                current_velocity = (current_velocity[0], current_velocity[1], 0.0)
        
        # Vérifier le statut du sol après toutes les sous-étapes
        ground_test = (current_position[0], current_position[1] - 0.1, current_position[2])
        final_collision_info['ground'] = self.collision_manager.check_block_collision(ground_test)
        
        # 4. Résultat: position corrigée et vitesse mise à jour
        return current_position, current_velocity, final_collision_info

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
_global_tick_physics_manager = None

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

def get_tick_physics_manager(world_blocks: Dict[Tuple[int, int, int], str]) -> TickBasedPhysicsManager:
    """Get or create global tick-based physics manager."""
    global _global_tick_physics_manager, _global_collision_manager
    collision_manager = get_collision_manager(world_blocks)
    if _global_tick_physics_manager is None or _global_tick_physics_manager.collision_manager != collision_manager:
        _global_tick_physics_manager = TickBasedPhysicsManager(collision_manager)
    return _global_tick_physics_manager

# ============================================================================
# UNIFIED API FUNCTIONS
# ============================================================================

def unified_check_collision(position: Tuple[float, float, float], 
                           world_blocks: Dict[Tuple[int, int, int], str],
                           other_players: List = None,
                           player_id: str = None) -> bool:
    """
    Unified collision check for both blocks and players.
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
