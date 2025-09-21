"""
Client module - imports from minecraft_client_fr.py for compatibility with tests.
"""

# Import only the necessary parts to avoid OpenGL dependencies in tests
from protocol import PlayerState, Cube
from collections import deque
import random

try:
    # Try to import OpenGL-dependent parts only when needed
    from minecraft_client_fr import EnhancedClientModel, cube_vertices as _cube_vertices
    OPENGL_AVAILABLE = True
except ImportError:
    # Fallback for testing without OpenGL
    OPENGL_AVAILABLE = False
    
    # Minimal ClientModel for testing
    class EnhancedClientModel:
        def __init__(self):
            self.world, self.shown, self._shown, self.sectors = {}, {}, {}, {}
            self.queue = deque()
            self.other_players = {}
            self.world_size, self.spawn_position = 128, [30, 50, 80]

class ClientModel(EnhancedClientModel):
    """Extended client model with local player cube support."""
    
    def __init__(self):
        super().__init__()
        self.local_player = None
        self.cubes = {}  # All cubes (local + remote)
        
    def create_local_player(self, player_id: str, position: tuple, rotation: tuple = (0, 0), name: str = None):
        """Create a local player as a cube."""
        self.local_player = PlayerState(player_id, position, rotation, name)
        self.local_player.is_local = True
        self.local_player.size = 0.4  # Default cube size from tests
        
        # Assign a unique color to the local player
        self.local_player.color = self._generate_player_color(player_id)
        
        # Add to cubes collection
        self.cubes[player_id] = self.local_player
        
        return self.local_player
    
    def add_cube(self, cube):
        """Add a cube (player) to the model."""
        if hasattr(cube, 'id'):
            # Set standard cube size if not already set
            if not hasattr(cube, 'size') or cube.size == 0.5:  # Default PlayerState size
                cube.size = 0.4  # Standard cube size for this system
            
            self.cubes[cube.id] = cube
            
            # Assign color if not already assigned
            if not hasattr(cube, 'color') or cube.color is None:
                cube.color = self._generate_player_color(cube.id)
            
            # Add to other_players if not local
            if not getattr(cube, 'is_local', False):
                self.other_players[cube.id] = cube
    
    def remove_cube(self, cube_id: str):
        """Remove a cube (player) from the model."""
        removed_cube = None
        if cube_id in self.cubes:
            removed_cube = self.cubes[cube_id]
            del self.cubes[cube_id]
        if cube_id in self.other_players:
            del self.other_players[cube_id]
        return removed_cube
    
    def get_all_cubes(self):
        """Get all cubes (local + remote players)."""
        return list(self.cubes.values())
    
    def get_other_cubes(self):
        """Get only remote player cubes (excluding local)."""
        return [cube for cube in self.cubes.values() if not getattr(cube, 'is_local', False)]
    
    def _generate_player_color(self, player_id: str):
        """Generate a unique color for a player based on their ID."""
        # Use a deterministic approach without affecting global random state
        colors = [
            (1.0, 0.3, 0.3),  # Red
            (0.3, 1.0, 0.3),  # Green  
            (0.3, 0.3, 1.0),  # Blue
            (1.0, 1.0, 0.3),  # Yellow
            (1.0, 0.3, 1.0),  # Magenta
            (0.3, 1.0, 1.0),  # Cyan
            (1.0, 0.6, 0.3),  # Orange
            (0.6, 0.3, 1.0),  # Purple
        ]
        
        # Select color based on hash without using random.seed()
        color_index = abs(hash(player_id)) % len(colors)
        return colors[color_index]

# Export the cube_vertices function
def cube_vertices(x, y, z, n):
    """Return vertices for a cube at position x, y, z with size 2*n."""
    if OPENGL_AVAILABLE:
        return _cube_vertices(x, y, z, n)
    else:
        # Fallback implementation for testing
        return [
            x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
            x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom  
            x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
            x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
            x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
            x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
        ]