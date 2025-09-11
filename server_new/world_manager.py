"""
World manager for server
Handles world generation, block management, and physics
"""

import asyncio
import logging
import math
import random
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import sys
import os

# Import noise generation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from noise_gen import NoiseGen


logger = logging.getLogger(__name__)


class Block:
    """Represents a block in the world"""
    def __init__(self, x: int, y: int, z: int, block_type: str):
        self.x = x
        self.y = y
        self.z = z
        self.block_type = block_type
        self.created_at = asyncio.get_event_loop().time()
    
    def to_dict(self):
        return {
            "pos": [self.x, self.y, self.z],
            "type": self.block_type
        }


class Chunk:
    """Represents a 16x16 chunk of blocks"""
    SIZE = 16
    
    def __init__(self, chunk_x: int, chunk_z: int):
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.blocks: Dict[Tuple[int, int, int], Block] = {}
        self.loaded = False
        self.dirty = False
    
    def add_block(self, block: Block):
        """Add a block to this chunk"""
        pos = (block.x, block.y, block.z)
        self.blocks[pos] = block
        self.dirty = True
    
    def remove_block(self, x: int, y: int, z: int) -> bool:
        """Remove a block from this chunk"""
        pos = (x, y, z)
        if pos in self.blocks:
            del self.blocks[pos]
            self.dirty = True
            return True
        return False
    
    def get_block(self, x: int, y: int, z: int) -> Optional[Block]:
        """Get a block from this chunk"""
        return self.blocks.get((x, y, z))
    
    def get_all_blocks(self) -> List[Block]:
        """Get all blocks in this chunk"""
        return list(self.blocks.values())


class WorldManager:
    """
    World manager with separated concerns
    Handles world generation, block management, and world physics
    """
    
    def __init__(self):
        # World data
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.loaded_chunks: Set[Tuple[int, int]] = set()
        
        # World generation
        self.world_size = 64
        self.noise_gen: Optional[NoiseGen] = None
        self.seed = 452692
        
        # Block types
        self.block_types = {
            "GRASS", "SAND", "BRICK", "STONE", "WOOD", "LEAF", "WATER"
        }
        
        # Physics constants
        self.gravity = 20.0
        self.water_level = 15
        
        # Generation parameters
        self.tree_chance = 0.01  # 1% chance
        self.hill_height_variance = 10
        
        logger.info("World manager initialized")
    
    async def generate_world(self, size: int = 64):
        """Generate the initial world"""
        self.world_size = size
        self.noise_gen = NoiseGen(self.seed)
        
        logger.info(f"Generating world of size {size}x{size}...")
        
        # Generate height map first
        height_map = await self._generate_height_map()
        
        # Generate terrain
        await self._generate_terrain(height_map)
        
        # Generate structures (trees, etc.)
        await self._generate_structures(height_map)
        
        block_count = sum(len(chunk.blocks) for chunk in self.chunks.values())
        logger.info(f"World generation complete: {block_count} blocks in {len(self.chunks)} chunks")
    
    async def _generate_height_map(self) -> Dict[Tuple[int, int], int]:
        """Generate height map using noise"""
        height_map = {}
        
        for x in range(0, self.world_size):
            for z in range(0, self.world_size):
                height = int(self.noise_gen.getHeight(x, z))
                height_map[(x, z)] = height
                
                # Yield control periodically for async operation
                if (x * self.world_size + z) % 100 == 0:
                    await asyncio.sleep(0)
        
        return height_map
    
    async def _generate_terrain(self, height_map: Dict[Tuple[int, int], int]):
        """Generate basic terrain (grass, stone, sand, water)"""
        blocks_processed = 0
        
        for (x, z), height in height_map.items():
            # Water level handling
            if height < self.water_level:
                # Sand beach
                self._set_block_direct(x, height, z, "SAND")
                
                # Fill with water
                for y in range(height + 1, self.water_level):
                    self._set_block_direct(x, y, z, "WATER")
            else:
                # Above water level
                if height < self.water_level + 3:
                    # Beach sand
                    self._set_block_direct(x, height, z, "SAND")
                else:
                    # Grass surface
                    self._set_block_direct(x, height, z, "GRASS")
                
                # Underground stone
                stone_depth = min(height - 1, height - random.randint(1, 3))
                for y in range(max(1, stone_depth), height):
                    self._set_block_direct(x, y, z, "STONE")
            
            blocks_processed += 1
            
            # Yield control periodically
            if blocks_processed % 50 == 0:
                await asyncio.sleep(0)
    
    async def _generate_structures(self, height_map: Dict[Tuple[int, int], int]):
        """Generate structures like trees"""
        structures_generated = 0
        
        for (x, z), height in height_map.items():
            # Only generate trees on grass and above water
            if height > self.water_level + 5:
                if random.random() < self.tree_chance:
                    await self._generate_tree(x, height, z)
                    structures_generated += 1
            
            # Yield control periodically
            if structures_generated % 5 == 0:
                await asyncio.sleep(0)
        
        logger.info(f"Generated {structures_generated} trees")
    
    async def _generate_tree(self, x: int, base_y: int, z: int):
        """Generate a tree at the specified position"""
        tree_height = random.randint(4, 6)
        
        # Tree trunk
        for y in range(base_y + 1, base_y + tree_height + 1):
            self._set_block_direct(x, y, z, "WOOD")
        
        # Tree leaves (simple sphere)
        leaf_y = base_y + tree_height
        leaf_radius = 2
        
        for lx in range(x - leaf_radius, x + leaf_radius + 1):
            for ly in range(leaf_y, leaf_y + 3):
                for lz in range(z - leaf_radius, z + leaf_radius + 1):
                    # Distance check for sphere shape
                    distance = math.sqrt((lx - x)**2 + (ly - leaf_y)**2 + (lz - z)**2)
                    if distance <= leaf_radius:
                        self._set_block_direct(lx, ly, lz, "LEAF")
    
    def _set_block_direct(self, x: int, y: int, z: int, block_type: str):
        """Set a block directly during world generation"""
        chunk_pos = self._get_chunk_position(x, z)
        chunk = self._get_or_create_chunk(chunk_pos)
        
        block = Block(x, y, z, block_type)
        chunk.add_block(block)
    
    def _get_chunk_position(self, x: int, z: int) -> Tuple[int, int]:
        """Get chunk position for world coordinates"""
        return x // Chunk.SIZE, z // Chunk.SIZE
    
    def _get_or_create_chunk(self, chunk_pos: Tuple[int, int]) -> Chunk:
        """Get or create a chunk at the specified position"""
        if chunk_pos not in self.chunks:
            chunk_x, chunk_z = chunk_pos
            self.chunks[chunk_pos] = Chunk(chunk_x, chunk_z)
        
        return self.chunks[chunk_pos]
    
    def set_block(self, position: Tuple[int, int, int], block_type: str) -> bool:
        """Set a block at the specified position"""
        x, y, z = position
        
        if not self._is_valid_position(x, y, z):
            return False
        
        chunk_pos = self._get_chunk_position(x, z)
        chunk = self._get_or_create_chunk(chunk_pos)
        
        block = Block(x, y, z, block_type)
        chunk.add_block(block)
        
        logger.debug(f"Set block {block_type} at ({x}, {y}, {z})")
        return True
    
    def remove_block(self, position: Tuple[int, int, int]) -> bool:
        """Remove a block at the specified position"""
        x, y, z = position
        
        chunk_pos = self._get_chunk_position(x, z)
        if chunk_pos not in self.chunks:
            return False
        
        chunk = self.chunks[chunk_pos]
        success = chunk.remove_block(x, y, z)
        
        if success:
            logger.debug(f"Removed block at ({x}, {y}, {z})")
        
        return success
    
    def get_block(self, position: Tuple[int, int, int]) -> Optional[Block]:
        """Get a block at the specified position"""
        x, y, z = position
        
        chunk_pos = self._get_chunk_position(x, z)
        if chunk_pos not in self.chunks:
            return None
        
        chunk = self.chunks[chunk_pos]
        return chunk.get_block(x, y, z)
    
    def has_block(self, position: Tuple[int, int, int]) -> bool:
        """Check if there's a block at the specified position"""
        return self.get_block(position) is not None
    
    def get_blocks_in_range(self, center: Tuple[float, float, float], radius: int = 50) -> List[Block]:
        """Get all blocks within a radius of a position"""
        cx, cy, cz = center
        blocks = []
        
        # Calculate chunk range
        min_chunk_x = int((cx - radius) // Chunk.SIZE)
        max_chunk_x = int((cx + radius) // Chunk.SIZE)
        min_chunk_z = int((cz - radius) // Chunk.SIZE)
        max_chunk_z = int((cz + radius) // Chunk.SIZE)
        
        # Check chunks in range
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_z in range(min_chunk_z, max_chunk_z + 1):
                chunk_pos = (chunk_x, chunk_z)
                if chunk_pos in self.chunks:
                    chunk = self.chunks[chunk_pos]
                    
                    # Check each block in the chunk
                    for block in chunk.get_all_blocks():
                        distance = math.sqrt(
                            (block.x - cx)**2 + (block.y - cy)**2 + (block.z - cz)**2
                        )
                        if distance <= radius:
                            blocks.append(block)
        
        return blocks
    
    def blocks_to_chunks(self, blocks: List[Block]) -> List[Tuple[int, int, List[dict]]]:
        """Convert blocks to chunk data for network transmission"""
        chunk_data: Dict[Tuple[int, int], List[dict]] = defaultdict(list)
        
        for block in blocks:
            chunk_pos = self._get_chunk_position(block.x, block.z)
            chunk_data[chunk_pos].append(block.to_dict())
        
        # Convert to list format
        result = []
        for (chunk_x, chunk_z), block_list in chunk_data.items():
            result.append((chunk_x, chunk_z, block_list))
        
        return result
    
    def can_place_block(self, position: Tuple[int, int, int], player_position: List[float]) -> bool:
        """Check if a block can be placed at the specified position"""
        x, y, z = position
        
        # Basic validation
        if not self._is_valid_position(x, y, z):
            return False
        
        # Check if position is not inside player
        px, py, pz = player_position
        player_distance = math.sqrt((x - px)**2 + (y - py)**2 + (z - pz)**2)
        if player_distance < 2.0:  # Too close to player
            return False
        
        # Check if there's already a block there
        if self.has_block(position):
            return False
        
        return True
    
    def _is_valid_position(self, x: int, y: int, z: int) -> bool:
        """Check if a position is valid for the world"""
        if y < 0 or y > 255:  # Standard Minecraft height limits
            return False
        
        # Check world bounds (if limited)
        world_bound = self.world_size + 10  # Allow some extra space
        if abs(x) > world_bound or abs(z) > world_bound:
            return False
        
        return True
    
    def get_height_at(self, x: int, z: int) -> int:
        """Get the height (top block) at the specified x, z coordinates"""
        chunk_pos = self._get_chunk_position(x, z)
        if chunk_pos not in self.chunks:
            return 0
        
        chunk = self.chunks[chunk_pos]
        max_height = 0
        
        for (bx, by, bz), block in chunk.blocks.items():
            if bx == x and bz == z:
                max_height = max(max_height, by)
        
        return max_height
    
    def get_block_count(self) -> int:
        """Get total number of blocks in the world"""
        return sum(len(chunk.blocks) for chunk in self.chunks.values())
    
    def get_chunk_count(self) -> int:
        """Get number of loaded chunks"""
        return len(self.chunks)
    
    def load_chunk(self, chunk_x: int, chunk_z: int):
        """Load a chunk (placeholder for persistent storage)"""
        chunk_pos = (chunk_x, chunk_z)
        if chunk_pos not in self.chunks:
            self.chunks[chunk_pos] = Chunk(chunk_x, chunk_z)
        
        self.loaded_chunks.add(chunk_pos)
    
    def unload_chunk(self, chunk_x: int, chunk_z: int):
        """Unload a chunk (placeholder for persistent storage)"""
        chunk_pos = (chunk_x, chunk_z)
        
        # In a real implementation, you might save the chunk to disk here
        # For now, we just mark it as unloaded but keep it in memory
        self.loaded_chunks.discard(chunk_pos)
    
    def get_stats(self) -> dict:
        """Get world statistics"""
        return {
            'world_size': self.world_size,
            'total_blocks': self.get_block_count(),
            'loaded_chunks': len(self.loaded_chunks),
            'total_chunks': self.get_chunk_count(),
            'seed': self.seed,
            'water_level': self.water_level
        }