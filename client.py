"""
Module client minimal.
"""

from protocol import PlayerState
from collections import deque

class EnhancedClientModel:
    """Modèle client minimal."""
    
    def __init__(self):
        self.world = {}
        self.shown = {}
        self.queue = deque()
        self.other_players = {}
    
    def add_block(self, position, block_type, immediate=True):
        """Ajoute un bloc au monde."""
        self.world[position] = block_type
    
    def remove_block(self, position, immediate=True):
        """Retire un bloc du monde."""
        if position in self.world:
            del self.world[position]

class ClientModel(EnhancedClientModel):
    """Modèle client étendu avec support joueur local."""
    
    def __init__(self):
        super().__init__()
        self.local_player = None
        self.cubes = {}
    
    def create_local_player(self, player_id: str, position, rotation=(0, 0), name=None):
        """Crée un joueur local."""
        self.local_player = PlayerState(player_id, position)
        self.local_player.is_local = True
        self.cubes[player_id] = self.local_player
        return self.local_player
    
    def add_cube(self, cube):
        """Ajoute un cube (joueur)."""
        if hasattr(cube, 'id'):
            self.cubes[cube.id] = cube
            if not getattr(cube, 'is_local', False):
                self.other_players[cube.id] = cube
    
    def remove_cube(self, cube_id: str):
        """Retire un cube (joueur)."""
        if cube_id in self.cubes:
            del self.cubes[cube_id]
        if cube_id in self.other_players:
            del self.other_players[cube_id]
    
    def get_all_cubes(self):
        """Obtient tous les cubes."""
        return list(self.cubes.values())

def cube_vertices(x, y, z, n):
    """Retourne les vertices d'un cube (version simplifiée)."""
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom  
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]