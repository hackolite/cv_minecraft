#!/usr/bin/env python3
"""
Client Minecraft Standalone - Version Autonome
==============================================

Un client Minecraft autonome qui fonctionne sans serveur avec:
- Support complet AZERTY/QWERTY
- Interface en français
- Génération de monde locale
- Physiques côté client
- Sauvegarde/chargement local

Usage:
    python3 minecraft_client_standalone.py [--config CONFIG_FILE]

Contrôles par défaut (AZERTY):
    Z/Q/S/D - Mouvement
    Espace - Saut
    Maj - S'accroupir
    R - Courir
    Tab - Voler
    F3 - Informations de debug
    Échap - Libérer la souris
    
Auteur: Assistant IA pour hackolite/cv_minecraft
"""

# Standard library imports
import sys, math, random, time, json, argparse, os, pickle
from collections import deque
from typing import Optional, Tuple, Dict, Any

# Third-party imports  
import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

# OpenGL constants fallback
try:
    GL_FOG
except NameError:
    from OpenGL.GL import (GL_FOG, GL_FOG_COLOR, GL_FOG_HINT, GL_DONT_CARE,
                          GL_FOG_MODE, GL_LINEAR, GL_FOG_START, GL_FOG_END,
                          GL_QUADS, GL_DEPTH_TEST, GL_PROJECTION, GL_MODELVIEW,
                          GL_FRONT_AND_BACK, GL_LINE, GL_FILL, GL_LINES,
                          GL_CULL_FACE, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                          GL_TEXTURE_MAG_FILTER, GL_NEAREST, GLfloat)
    from OpenGL.GLU import gluPerspective

# Local imports
from client_config import config
from protocol import PlayerState, BlockType
from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT, GRAVITY, TERMINAL_VELOCITY, JUMP_VELOCITY,
    unified_check_collision
)
from noise_gen import NoiseGen

# ============================================================================
# CONSTANTS
# ============================================================================

TICKS_PER_SEC = 60
WALKING_SPEED = 5
FLYING_SPEED = 15

# Size of sectors used to batch GL calls
SECTOR_SIZE = 16

# Brouillard
FOG_DISTANCE = 60.0

# Sprint FOV boost
SPRINT_FOV = 10

# Texture path
TEXTURE_PATH = 'texture.png'

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize(position):
    """Normalize position to block coordinates."""
    return tuple(int(round(x)) for x in position)

def sectorize(position):
    """Return sector that contains the given position."""
    x, y, z = normalize(position)
    return (x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE)

def cube_vertices(x, y, z, n):
    """Return vertices for a cube at position x, y, z with size 2*n."""
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom  
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]

# Texture coordinates
def tex_coord(x, y, n=4):
    """Return texture coordinates for a square."""
    m = 1.0 / n
    dx, dy = x * m, y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side):
    """Return list of texture coordinates for the top, bottom and side."""
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)      # top
    result.extend(bottom)   # bottom
    result.extend(side)     # left
    result.extend(side)     # right
    result.extend(side)     # front
    result.extend(side)     # back
    return result

# Block texture mappings
TEXTURE_MAP = {
    BlockType.GRASS: tex_coords((1, 0), (0, 1), (0, 0)),
    BlockType.SAND: tex_coords((1, 1), (1, 1), (1, 1)),
    BlockType.BRICK: tex_coords((2, 0), (2, 0), (2, 0)),
    BlockType.STONE: tex_coords((2, 1), (2, 1), (2, 1)),
    BlockType.WOOD: tex_coords((3, 1), (3, 1), (3, 0)),
    BlockType.LEAF: tex_coords((3, 2), (3, 2), (3, 2)),
}

# ============================================================================
# STANDALONE CLIENT MODEL
# ============================================================================

class StandaloneClientModel:
    """Modèle client autonome avec génération de monde locale."""
    
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        try:
            self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())
        except Exception as e:
            print(f"Erreur texture: {e}")
            self.group = None
        
        # Données du monde
        self.world = {}  # position -> block_type
        self.shown = {}  # position -> vertex_list
        self._shown = {}  # sector -> set of positions
        self.sectors = {}  # sector -> set of positions
        self.queue = deque()
        
        # Génération de monde
        self.world_size = 128
        self.spawn_position = [64, 100, 64]
        self.noise_gen = NoiseGen()
        
        # Physics
        self.collision_detector = None
        self.physics = None
        
        # Generate initial world
        self.generate_world()
    
    def generate_world(self):
        """Génère un monde initial."""
        print("🌍 Génération du monde...")
        
        # Generate terrain using noise
        for x in range(-self.world_size // 2, self.world_size // 2):
            for z in range(-self.world_size // 2, self.world_size // 2):
                # Get terrain height from noise
                height = int(self.noise_gen.get_noise(x, z) * 20) + 50
                
                # Add bedrock layer
                for y in range(0, 5):
                    self.add_block((x, y, z), BlockType.STONE, immediate=False)
                
                # Add stone layers
                for y in range(5, height - 5):
                    self.add_block((x, y, z), BlockType.STONE, immediate=False)
                
                # Add dirt layer
                for y in range(height - 5, height - 1):
                    self.add_block((x, y, z), BlockType.SAND, immediate=False)
                
                # Add grass on top
                self.add_block((x, height - 1, z), BlockType.GRASS, immediate=False)
                
                # Occasionally add trees
                if random.random() < 0.02 and height > 45:
                    tree_height = random.randint(3, 6)
                    # Tree trunk
                    for y in range(height, height + tree_height):
                        self.add_block((x, y, z), BlockType.WOOD, immediate=False)
                    # Tree leaves
                    for dx in range(-2, 3):
                        for dz in range(-2, 3):
                            for dy in range(tree_height - 1, tree_height + 2):
                                if random.random() < 0.7:
                                    self.add_block((x + dx, height + dy, z + dz), BlockType.LEAF, immediate=False)
        
        # Set a safe spawn position
        self.spawn_position = [0, self.get_ground_height(0, 0) + 3, 0]
        
        print(f"✅ Monde généré avec {len(self.world)} blocs")
    
    def get_ground_height(self, x, z):
        """Trouve la hauteur du sol à une position donnée."""
        for y in range(100, 0, -1):
            if (x, y, z) in self.world:
                return y + 1
        return 50  # Default height
    
    def add_block(self, position, block_type, immediate=True):
        """Ajoute un bloc au monde."""
        if position in self.world:
            self.remove_block(position, immediate)
        
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), set()).add(position)
        
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)
    
    def remove_block(self, position, immediate=True):
        """Retire un bloc du monde."""
        if position not in self.world:
            return
        
        del self.world[position]
        
        # Remove from sectors
        sector = sectorize(position)
        if sector in self.sectors:
            self.sectors[sector].discard(position)
            if not self.sectors[sector]:
                del self.sectors[sector]
        
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)
    
    def check_neighbors(self, position):
        """Vérifie les voisins d'un bloc après modification."""
        x, y, z = position
        for dx, dy, dz in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
            neighbor = (x+dx, y+dy, z+dz)
            if neighbor in self.world:
                if self.exposed(neighbor):
                    if neighbor not in self.shown:
                        self.show_block(neighbor)
                else:
                    if neighbor in self.shown:
                        self.hide_block(neighbor)
    
    def neighbors(self, position):
        """Retourne les voisins d'un bloc."""
        x, y, z = position
        return [(x+dx, y+dy, z+dz) for dx, dy, dz in 
                [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]]
    
    def exposed(self, position):
        """Vérifie si un bloc est exposé (visible)."""
        if position not in self.world:
            return False
        
        x, y, z = position
        for dx, dy, dz in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
            neighbor = (x+dx, y+dy, z+dz)
            if neighbor not in self.world:
                return True
        return False
    
    def show_block(self, position, immediate=True):
        """Affiche un bloc."""
        if position in self.shown:
            return
        
        if position not in self.world:
            return
        
        block_type = self.world[position]
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = TEXTURE_MAP.get(block_type, TEXTURE_MAP[BlockType.STONE])
        
        if immediate:
            self.shown[position] = self.batch.add(24, GL_QUADS, self.group,
                ('v3f/static', vertex_data),
                ('t2f/static', texture_data))
        else:
            self.enqueue(self._show_block, position, vertex_data, texture_data)
    
    def _show_block(self, position, vertex_data, texture_data):
        """Affiche un bloc (version interne)."""
        self.shown[position] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))
    
    def hide_block(self, position):
        """Cache un bloc."""
        if position in self.shown:
            self.shown[position].delete()
            del self.shown[position]
    
    def enqueue(self, func, *args):
        """Ajoute une opération à la queue de rendu."""
        self.queue.append((func, args))
    
    def process_queue(self):
        """Traite la queue de rendu."""
        start = time.time()
        while self.queue and time.time() - start < 1.0 / TICKS_PER_SEC:
            func, args = self.queue.popleft()
            func(*args)
    
    def process_entire_queue(self):
        """Traite toute la queue."""
        while self.queue:
            func, args = self.queue.popleft()
            func(*args)
    
    def hit_test(self, position, vector, max_distance=8):
        """Test de collision pour la visée."""
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in range(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None
    
    def change_sectors(self, before, after):
        """Change les secteurs visibles."""
        before_set = set()
        after_set = set()
        pad = 4
        for dx in range(-pad, pad + 1):
            for dy in range(-pad, pad + 1):
                for dz in range(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        
        show = after_set - before_set
        hide = before_set - after_set
        
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)
    
    def show_sector(self, sector):
        """Affiche un secteur."""
        if sector not in self.sectors:
            return
        
        for position in self.sectors[sector]:
            if position not in self.shown and self.exposed(position):
                self.show_block(position, immediate=False)
    
    def hide_sector(self, sector):
        """Cache un secteur."""
        if sector not in self.sectors:
            return
        
        for position in self.sectors[sector]:
            if position in self.shown:
                self.hide_block(position)
    
    def save_world(self, filename="world.dat"):
        """Sauvegarde le monde."""
        try:
            with open(filename, 'wb') as f:
                pickle.dump({
                    'world': self.world,
                    'spawn_position': self.spawn_position
                }, f)
            print(f"💾 Monde sauvegardé: {filename}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    
    def load_world(self, filename="world.dat"):
        """Charge un monde."""
        try:
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                    self.world = data['world']
                    self.spawn_position = data['spawn_position']
                    
                    # Rebuild sectors
                    self.sectors = {}
                    for position in self.world:
                        self.sectors.setdefault(sectorize(position), set()).add(position)
                    
                    print(f"📁 Monde chargé: {filename}")
                    return True
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
        return False

# ============================================================================
# STANDALONE MINECRAFT WINDOW
# ============================================================================

class StandaloneMinecraftWindow(pyglet.window.Window):
    """Fenêtre de jeu autonome."""
    
    def __init__(self, *args, **kwargs):
        """Initialise la fenêtre de jeu."""
        super().__init__(*args, **kwargs)
        
        # Configuration exclusive mouse
        self.exclusive = False
        
        # Modèle de monde
        self.model = StandaloneClientModel()
        
        # Position et orientation du joueur
        self.position = tuple(self.model.spawn_position)
        self.rotation = (0, 0)
        
        # Mouvement
        self.strafe = [0, 0]
        self.dy = 0  # Vitesse verticale
        self.jumping = False
        self.flying = False
        self.sprinting = False
        self.crouch = False
        self.on_ground = True
        
        # Configuration vitesses
        self.movement_speed = config.get("player", "movement_speed", 5.0)
        self.jump_speed = config.get("player", "jump_speed", 8.0)
        self.flying_speed = config.get("player", "flying_speed", 15.0)
        
        # Inventaire
        self.inventory = [BlockType.BRICK, BlockType.GRASS, BlockType.SAND, BlockType.STONE, BlockType.WOOD]
        self.block = self.inventory[0]
        
        # Touches de mouvement configurables
        layout = config.get("controls", "keyboard_layout", "azerty")
        if layout == "qwerty":
            self.movement_keys = {"forward": "W", "backward": "S", "left": "A", "right": "D"}
        else:  # azerty
            self.movement_keys = {"forward": "Z", "backward": "S", "left": "Q", "right": "D"}
        
        # Interface
        self.show_debug = config.get("interface", "show_debug_info", True)
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
                                     x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
                                     color=(255, 255, 255, 255))
        
        # Messages temporaires
        self.message_label = pyglet.text.Label('', font_name='Arial', font_size=16,
                                             x=self.width // 2, y=self.height - 50,
                                             anchor_x='center', anchor_y='top',
                                             color=(255, 255, 0, 255))
        self.message_timer = 0
        
        # FOV et viseur
        self.fov_offset = 0
        self.setup_crosshair()
        
        # Secteur actuel
        self.sector = None
        
        # Physics
        self.collision_detector = MinecraftCollisionDetector(self.model.world)
        self.physics = MinecraftPhysics(self.collision_detector)
        
        # Temps pour mise à jour physique
        self.last_physics_update = time.time()
        
        # Configuration initiale
        self.set_exclusive_mouse(True)
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
    
    def setup_crosshair(self):
        """Configure le viseur."""
        x, y = self.width // 2, self.height // 2
        n = 10  # Taille du viseur
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )
    
    def set_exclusive_mouse(self, exclusive):
        """Active/désactive l'exclusivité de la souris."""
        super().set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
    
    def get_sight_vector(self):
        """Retourne le vecteur de visée normalisé."""
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)
    
    def get_motion_vector(self):
        """Retourne le vecteur de mouvement basé sur les touches pressées."""
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy -= 0.2
                elif self.strafe[0] < 0:
                    dy += 0.2
            else:
                dy = 0.0
                m = 1
            dx = math.cos(x_angle) * m
            dz = math.sin(x_angle) * m
        else:
            dx = dy = dz = 0.0
        return (dx, dy, dz)
    
    def update(self, dt):
        """Mise à jour principale du jeu."""
        # Traite la queue de rendu
        self.model.process_queue()
        
        # Met à jour les secteurs
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        
        # Met à jour la physique
        self._update_physics(dt)
        
        # Met à jour l'interface
        self.update_ui()
        self.update_message_display()
    
    def _update_physics(self, dt):
        """Met à jour la physique du joueur."""
        dt = min(dt, 0.2)  # Évite les gros sauts temporels
        
        # Calcule le mouvement voulu
        dx, dy, dz = self.get_motion_vector()
        
        # Applique la vitesse de mouvement
        if self.flying:
            speed = self.flying_speed
        elif self.sprinting:
            speed = self.movement_speed * 1.5
        elif self.crouch:
            speed = self.movement_speed * 0.5
        else:
            speed = self.movement_speed
        
        # Applique le mouvement horizontal
        dx, dz = dx * dt * speed, dz * dt * speed
        
        # Gère le saut
        if self.jumping and self.on_ground and not self.flying:
            self.dy = self.jump_speed
            self.on_ground = False
        
        # Applique la gravité si pas en vol
        if not self.flying:
            self.dy -= GRAVITY * dt
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
        else:
            # En vol, utilise le mouvement vertical direct
            self.dy = dy * speed
        
        # Applique le mouvement vertical
        dy = self.dy * dt
        
        # Met à jour la détection de collision avec le monde actuel
        self.collision_detector.world_blocks = self.model.world
        
        # Utilise le système de physique pour le mouvement
        old_position = self.position
        new_position, new_velocity, new_on_ground = self.physics.update_position(
            self.position, (dx/dt, self.dy, dz/dt), dt, self.on_ground, self.jumping
        )
        
        # Met à jour l'état du joueur
        self.position = new_position
        if not self.flying:
            self.dy = new_velocity[1]
            self.on_ground = new_on_ground
    
    def collide(self, position, height):
        """Vérifie les collisions à une position donnée."""
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)]:
            for i in range(3):
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in range(height):
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) in self.model.world:
                        return True
        return False
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Gère les clics de souris."""
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if button == mouse.LEFT and block:
                self.model.remove_block(block)
            elif button == mouse.RIGHT and previous:
                self.model.add_block(previous, self.block)
        else:
            self.set_exclusive_mouse(True)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Gère le mouvement de la souris."""
        if self.exclusive:
            m = config.get("controls", "mouse_sensitivity", 0.15)
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)
    
    def on_key_press(self, symbol, modifiers):
        """Gère les touches pressées."""
        # Mouvement selon le layout clavier configuré
        if symbol == getattr(key, self.movement_keys["forward"]):
            self.strafe[0] -= 1
        elif symbol == getattr(key, self.movement_keys["backward"]):
            self.strafe[0] += 1
        elif symbol == getattr(key, self.movement_keys["left"]):
            self.strafe[1] -= 1
        elif symbol == getattr(key, self.movement_keys["right"]):
            self.strafe[1] += 1
        
        # Autres contrôles
        elif symbol == key.SPACE:
            self.jumping = True
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.LSHIFT:
            self.crouch = True
            if self.sprinting:
                self.fov_offset -= SPRINT_FOV
                self.sprinting = False
        elif symbol == key.R:
            if not self.crouch:
                if not self.sprinting:
                    self.fov_offset += SPRINT_FOV
                self.sprinting = True
        elif symbol == key.TAB:
            self.flying = not self.flying
            status = "Vol activé" if self.flying else "Vol désactivé"
            self.show_message(status)
        elif symbol == key.F3:
            self.show_debug = not self.show_debug
        elif symbol == key.F5:
            self.model.save_world()
            self.show_message("💾 Monde sauvegardé")
        elif symbol == key.F9:
            if self.model.load_world():
                self.show_message("📁 Monde chargé")
                # Rebuild graphics
                self.sector = None
                sector = sectorize(self.position)
                self.model.change_sectors(None, sector)
                self.model.process_entire_queue()
            else:
                self.show_message("❌ Échec du chargement")
        
        # Sélection de bloc (1-5)
        elif key._1 <= symbol <= key._5:
            index = symbol - key._1
            if index < len(self.inventory):
                self.block = self.inventory[index]
                self.show_message(f"Bloc sélectionné: {self.block}")
    
    def on_key_release(self, symbol, modifiers):
        """Gère les touches relâchées."""
        # Mouvement
        if symbol == getattr(key, self.movement_keys["forward"]):
            self.strafe[0] += 1
        elif symbol == getattr(key, self.movement_keys["backward"]):
            self.strafe[0] -= 1
        elif symbol == getattr(key, self.movement_keys["left"]):
            self.strafe[1] += 1
        elif symbol == getattr(key, self.movement_keys["right"]):
            self.strafe[1] -= 1
        elif symbol == key.SPACE:
            self.jumping = False
        elif symbol == key.LSHIFT:
            self.crouch = False
    
    def on_resize(self, width, height):
        """Gère le redimensionnement de la fenêtre."""
        # Met à jour les labels
        self.label.y = height - 10
        self.message_label.x = width // 2
        self.message_label.y = height - 50
        
        # Recrée le viseur
        if self.reticle:
            self.reticle.delete()
        self.setup_crosshair()
        
        # Sauvegarde la nouvelle taille
        config.set("graphics", "window_width", width)
        config.set("graphics", "window_height", height)
    
    def set_3d(self):
        """Configure OpenGL pour le rendu 3D."""
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70.0 + self.fov_offset, width / float(height), 0.1, FOG_DISTANCE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)
    
    def set_2d(self):
        """Configure OpenGL pour le rendu 2D."""
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def on_draw(self):
        """Rendu principal."""
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        
        # Rendu du monde
        self.model.batch.draw()
        
        # Rendu du bloc visé
        self.draw_focused_block()
        
        # Interface 2D
        self.set_2d()
        self.draw_ui()
    
    def draw_focused_block(self):
        """Dessine les contours du bloc visé."""
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    def update_ui(self):
        """Met à jour l'interface utilisateur."""
        if not self.show_debug:
            self.label.text = ""
            return
        
        x, y, z = self.position
        visible_blocks = len(self.model.shown)
        total_blocks = len(self.model.world)
        
        # Indicateurs d'état
        status_indicators = []
        if self.flying:
            status_indicators.append("✈️ Vol")
        if self.sprinting:
            status_indicators.append("🏃 Sprint")
        if self.crouch:
            status_indicators.append("🐢 Accroupi")
        if not self.on_ground:
            status_indicators.append("🌊 En l'air")
        
        status_text = " | ".join(status_indicators) if status_indicators else "🚶 Normal"
        
        self.label.text = (
            f"Client Minecraft Standalone v1.0\n"
            f"Position: X={x:.1f}, Y={y:.1f}, Z={z:.1f}\n"
            f"Rotation: H={self.rotation[0]:.1f}°, V={self.rotation[1]:.1f}°\n"
            f"Blocs: {visible_blocks:,} visibles / {total_blocks:,} total\n"
            f"Secteur: {sectorize(self.position)}\n"
            f"État: {status_text}\n"
            f"Bloc sélectionné: {self.block}\n"
            f"F3: Debug | F5: Sauvegarder | F9: Charger | Tab: Vol"
        )
    
    def update_message_display(self):
        """Met à jour l'affichage des messages temporaires."""
        if self.message_timer > 0:
            self.message_timer -= 1.0 / TICKS_PER_SEC
            if self.message_timer <= 0:
                self.message_label.text = ""
    
    def show_message(self, text, duration=3.0):
        """Affiche un message temporaire."""
        self.message_label.text = text
        self.message_timer = duration
    
    def draw_ui(self):
        """Dessine l'interface utilisateur."""
        # Informations de debug
        self.label.draw()
        
        # Messages temporaires
        self.message_label.draw()
        
        # Viseur
        glColor3d(1, 1, 1)
        self.reticle.draw(GL_LINES)


def setup_opengl():
    """Configuration OpenGL de base."""
    glClearColor(0.5, 0.69, 1.0, 1)  # Ciel bleu
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    
    # Brouillard optionnel
    try:
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
        glHint(GL_FOG_HINT, GL_DONT_CARE)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, 40.0)
        glFogf(GL_FOG_END, 60.0)
    except:
        pass


def parse_args():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="Client Minecraft autonome")
    parser.add_argument('--config', '-c', default='client_config.json', help='Fichier de configuration')
    parser.add_argument('--fullscreen', '-f', action='store_true', help='Démarrer en plein écran')
    parser.add_argument('--debug', '-d', action='store_true', help='Activer le mode debug')
    parser.add_argument('--world', '-w', help='Fichier de monde à charger')
    return parser.parse_args()


def main():
    """Point d'entrée principal du client autonome."""
    print("🎮 Client Minecraft Standalone - Démarrage...")
    args = parse_args()
    
    # Charge la configuration si différente
    if args.config != 'client_config.json':
        global config
        from client_config import ClientConfig
        config = ClientConfig(args.config)
    
    # Applique les arguments
    for key, setting in [("fullscreen", ("graphics", "fullscreen")), 
                        ("debug", ("interface", "show_debug_info"))]:
        if getattr(args, key):
            config.set(setting[0], setting[1], True)
    
    # Configuration de la fenêtre
    width = config.get("graphics", "window_width", 1280)
    height = config.get("graphics", "window_height", 720)
    fullscreen = config.get("graphics", "fullscreen", False)
    
    # Crée la fenêtre
    try:
        setup_opengl()
        window = StandaloneMinecraftWindow(
            width=width, height=height,
            caption='Minecraft Client Standalone',
            resizable=True, fullscreen=fullscreen
        )
        
        # Charge un monde spécifique si demandé
        if args.world and window.model.load_world(args.world):
            print(f"📁 Monde chargé: {args.world}")
        
        print("✅ Client Minecraft Standalone prêt!")
        print("🎮 Contrôles: Z/Q/S/D mouvement, Espace saut, Tab vol, F3 debug")
        print("📦 Construction: Clic gauche détruire, clic droit placer")
        print("💾 Sauvegarde: F5 sauvegarder, F9 charger")
        
        pyglet.app.run()
        
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())