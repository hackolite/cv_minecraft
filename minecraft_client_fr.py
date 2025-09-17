#!/usr/bin/env python3
"""
Client Minecraft Amélioré avec Support Français
===============================================

Un client Minecraft amélioré utilisant Pyglet avec:
- Support complet AZERTY/QWERTY
- Interface en français
- Gestion d'erreurs améliorée
- Configuration flexible
- Reconnexion automatique
- Indicateurs de performance

Usage:
    python3 minecraft_client_fr.py [--server HOST:PORT] [--config CONFIG_FILE]

Contrôles par défaut (AZERTY):
    Z/Q/S/D - Mouvement
    Espace - Saut
    Maj - S'accroupir
    R - Courir
    Tab - Voler
    T - Chat (bientôt)
    E - Inventaire (bientôt)
    F3 - Informations de debug
    Échap - Libérer la souris
    
Auteur: Assistant IA pour hackolite/cv_minecraft
"""

# Standard library imports
import sys, math, random, time, json, argparse, asyncio, threading
from collections import deque
from typing import Optional, Tuple, Dict, Any

# Third-party imports  
import pyglet, websockets
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
                          GL_NEAREST, GL_TEXTURE_MAG_FILTER, GLfloat)

# Project imports
from protocol import *
from client_config import config

# Game constants  
TICKS_PER_SEC, WALKING_SPEED, FLYING_SPEED = 60, 5, 15
JUMP_SPEED, TERMINAL_VELOCITY, GRAVITY = 8.0, 50, 20.0
PLAYER_HEIGHT, PLAYER_FOV, SPRINT_FOV = 2, 70.0, 10.0
TEXTURE_PATH = 'texture.png'

# Python 2/3 compatibility
xrange = range

# Utility constants and functions
FACES = [(0, 1, 0), (0, -1, 0), (-1, 0, 0), (1, 0, 0), (0, 0, 1), (0, 0, -1)]

def normalize(position):
    """Normalize position to block coordinates."""
    return tuple(int(round(x)) for x in position)

def sectorize(position):
    """Return sector that contains the given position."""
    x, y, z = normalize(position)
    return (x // 16, 0, z // 16)

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

def check_player_collision(position, player_size, other_players):
    """Check if player at position collides with other players."""
    px, py, pz = position
    for other_player in other_players:
        if not isinstance(other_player, PlayerState):
            continue
        ox, oy, oz = other_player.position
        other_size = other_player.size
        # Check 3D bounding box collision
        if all((px - player_size) < (ox + other_size) and (px + player_size) >= (ox - other_size)
               for px, ox, player_size, other_size in [(px, ox, player_size, other_size),
                                                       (py, oy, player_size, other_size), 
                                                       (pz, oz, player_size, other_size)]):
            return True
    return False

def check_player_collision_with_direction(position, player_size, other_players):
    """Check if player at position collides with other players and return collision direction.
    
    Returns:
        dict: {
            'collision': bool,
            'top': bool,     # True if standing on top of another player
            'bottom': bool,  # True if another player is on top
            'side': bool     # True if side collision
        }
    """
    px, py, pz = position
    result = {'collision': False, 'top': False, 'bottom': False, 'side': False}
    
    for other_player in other_players:
        if not isinstance(other_player, PlayerState):
            continue
        ox, oy, oz = other_player.position
        other_size = other_player.size
        
        # Check 3D bounding box collision
        x_overlap = (px - player_size) < (ox + other_size) and (px + player_size) >= (ox - other_size)
        y_overlap = (py - player_size) < (oy + other_size) and (py + player_size) >= (oy - other_size)
        z_overlap = (pz - player_size) < (oz + other_size) and (pz + player_size) >= (oz - other_size)
        
        if x_overlap and y_overlap and z_overlap:
            result['collision'] = True
            
            # Determine collision direction based on relative Y positions
            # Top collision: current player is standing on another player
            # This happens when the player is above the other player
            if py > oy:  # Current player center is above other player center
                result['top'] = True
            # Bottom collision: another player is on top of current player  
            elif py < oy:  # Current player center is below other player center
                result['bottom'] = True
            else:
                result['side'] = True
    
    return result

class AdvancedNetworkClient:
    """Client réseau simplifié avec reconnexion automatique."""
    
    def __init__(self, window, server_url: str = None):
        self.window = window
        self.server_url = server_url or config.get_server_url()
        self.websocket = None
        self.connected = False
        self.loop = None
        self.thread = None
        self.player_id = None
        self.connection_attempts = 0
        self.max_attempts = config.get("server", "max_connection_attempts", 5)
        self.reconnect_delay = 5
        self.ping_ms = 0
        self.messages_sent = self.messages_received = 0
        
    def start_connection(self):
        """Démarre la connexion réseau dans un thread séparé."""
        if not (self.thread and self.thread.is_alive()):
            self.thread = threading.Thread(target=self._run_network_thread, daemon=True)
            self.thread.start()
            print(config.get_localized_text("connecting"))
    
    def _run_network_thread(self):
        """Thread principal de gestion réseau."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connection_manager())
        except Exception as e:
            print(f"Erreur réseau: {e}")
        finally:
            self.loop.close()
    
    async def _connection_manager(self):
        """Gestionnaire de connexion avec reconnexion automatique."""
        while self.connection_attempts < self.max_attempts:
            try:
                await self._connect_to_server()
                break
            except Exception:
                self.connected = False
                self.connection_attempts += 1
                if config.get("server", "auto_reconnect", True) and self.connection_attempts < self.max_attempts:
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 1.5, 30)
    
    async def _connect_to_server(self):
        """Se connecte au serveur et gère les messages."""
        timeout = config.get("server", "connection_timeout", 10)
        self.websocket = await asyncio.wait_for(websockets.connect(self.server_url), timeout=timeout)
        self.connected = True
        self.connection_attempts = 0
        self.reconnect_delay = 5
        
        # Envoi du message de connexion
        join_msg = create_player_join_message(config.get("player", "name", "Joueur"))
        await self.websocket.send(join_msg.to_json())
        self.messages_sent += 1
        
        # Gestion des messages et ping
        ping_task = asyncio.create_task(self._ping_loop())
        try:
            async for message_str in self.websocket:
                try:
                    message = Message.from_json(message_str)
                    self.messages_received += 1
                    pyglet.clock.schedule_once(lambda dt, msg=message: self._handle_server_message(msg), 0)
                except Exception:
                    pass
        finally:
            ping_task.cancel()
            self.connected = False
            self.websocket = None
    
    async def _ping_loop(self):
        """Boucle de ping pour mesurer la latence."""
        while self.connected and self.websocket:
            try:
                start = time.time()
                await self.websocket.ping()
                self.ping_ms = int((time.time() - start) * 1000)
                await asyncio.sleep(5)
            except:
                break
    
    def _handle_server_message(self, message: Message):
        """Gère un message du serveur (appelé sur le thread principal)."""
        try:
            if message.type == MessageType.WORLD_INIT:
                self.window.model.load_world_data(message.data)
            elif message.type == MessageType.WORLD_CHUNK:
                self.window.model.load_world_chunk(message.data)
            elif message.type == MessageType.WORLD_UPDATE:
                for block_data in message.data.get("blocks", []):
                    block_update = BlockUpdate.from_dict(block_data)
                    if block_update.block_type == BlockType.AIR:
                        self.window.model.remove_block(block_update.position)
                    else:
                        self.window.model.add_block(block_update.position, block_update.block_type)
            elif message.type == MessageType.PLAYER_UPDATE:
                player_data = message.data
                player_id = player_data["id"]
                if player_id == self.player_id:
                    self.window.position = tuple(player_data["position"])
                    self.window.dy = player_data["velocity"][1]
                    self.window.on_ground = player_data.get("on_ground", False)
                else:
                    self.window.model.other_players[player_id] = PlayerState.from_dict(player_data)
            elif message.type == MessageType.PLAYER_LIST:
                self.window.model.other_players = {}
                for player_data in message.data.get("players", []):
                    player = PlayerState.from_dict(player_data)
                    if player.id != self.player_id:
                        self.window.model.other_players[player.id] = player
            elif message.type == MessageType.CHAT_BROADCAST:
                self.window.show_message(f"[CHAT] {message.data.get('text', '')}")
            elif message.type == MessageType.ERROR:
                self.window.show_message(f"{config.get_localized_text('server_error')}: {message.data.get('message', 'Erreur inconnue')}")
        except Exception as e:
            print(f"Erreur message {message.type}: {e}")
    
    def send_message(self, message: Message):
        """Envoie un message au serveur."""
        if self.connected and self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(self._send_message_async(message), self.loop)
            return True
        return False
    
    async def _send_message_async(self, message: Message):
        """Envoie un message de manière asynchrone."""
        if self.websocket:
            try:
                await self.websocket.send(message.to_json())
                self.messages_sent += 1
            except Exception as e:
                print(f"Erreur envoi: {e}")
    
    def get_connection_stats(self):
        """Retourne les statistiques de connexion."""
        return {
            "connected": self.connected,
            "ping_ms": self.ping_ms,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "connection_attempts": self.connection_attempts,
            "server_url": self.server_url
        }
    
    def disconnect(self):
        """Se déconnecte du serveur."""
        if self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
        self.connected = False


class EnhancedClientModel:
    """Modèle client simplifié avec gestion optimisée des blocs."""
    
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        try:
            self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())
        except Exception as e:
            print(f"Erreur texture: {e}")
            self.group = None
        
        # Données du monde
        self.world, self.shown, self._shown, self.sectors = {}, {}, {}, {}
        self.queue = deque()
        self.other_players = {}
        self.world_size, self.spawn_position = 128, [30, 50, 80]
    
    def load_world_data(self, world_data):
        """Charge les données initiales du monde depuis le serveur."""
        self.world_size = world_data.get("world_size", 128)
        self.spawn_position = world_data.get("spawn_position", [30, 50, 80])
    
    def load_world_chunk(self, chunk_data):
        """Charge un chunk de données du monde."""
        for pos_str, block_type in chunk_data.get("blocks", {}).items():
            try:
                position = tuple(map(int, pos_str.split(',')))
                self.add_block(position, block_type, immediate=False)
            except ValueError:
                continue
    
    def add_block(self, position, block_type, immediate=True):
        """Ajoute un bloc au monde."""
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        action = self.show_block if self.exposed(position) else lambda p: None
        (action(position) if immediate else self.enqueue(action, position))
    
    def remove_block(self, position, immediate=True):
        """Retire un bloc du monde."""
        del self.world[position]
        self.hide_block(position)
        neighbors = [n for n in self.neighbors(position) if n in self.world and n not in self.shown and self.exposed(n)]
        if immediate:
            for neighbor in neighbors:
                self.show_block(neighbor)
        else:
            for neighbor in neighbors:
                self.enqueue(self.show_block, neighbor)
    
    def neighbors(self, position):
        """Retourne les voisins d'un bloc."""
        x, y, z = position
        return [(x + dx, y + dy, z + dz) for dx, dy, dz in FACES]
    
    def exposed(self, position):
        """Vérifie si un bloc est exposé (visible)."""
        x, y, z = position
        return any((x + dx, y + dy, z + dz) not in self.world for dx, dy, dz in FACES)
    
    def show_block(self, position, immediate=True):
        """Affiche un bloc."""
        block_type = self.world.get(position)
        if not (block_type and position not in self.shown and self.group):
            return
            
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(block_texture_data(block_type))
        
        try:
            self._shown[position] = self.batch.add(24, GL_QUADS, self.group,
                                                  ('v3f/static', vertex_data), ('t2f/static', texture_data))
            self.shown[position] = block_type
        except Exception:
            pass
    
    def hide_block(self, position):
        """Cache un bloc."""
        if position in self.shown:
            if position in self._shown:
                self._shown[position].delete()
                del self._shown[position]
            del self.shown[position]
    
    def enqueue(self, func, *args):
        """Ajoute une opération à la queue de rendu."""
        self.queue.append((func, args))
    
    def process_queue(self):
        """Traite la queue de rendu."""
        start = time.process_time()
        while self.queue and time.process_time() - start < 1.0 / TICKS_PER_SEC:
            func, args = self.queue.popleft()
            func(*args)
    
    def process_entire_queue(self):
        """Traite toute la queue."""
        while self.queue:
            func, args = self.queue.popleft()
            func(*args)
    
    def hit_test(self, position, vector, max_distance=8):
        """Test de collision pour la visée."""
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        m = 8
        
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None
    
    def change_sectors(self, before, after):
        """Change les secteurs visibles."""
        pad = 4
        before_set = set()
        after_set = set()
        
        if before:
            x, _, z = before
            before_set = {(x + dx, 0, z + dz) for dx in xrange(-pad, pad + 1) for dz in xrange(-pad, pad + 1)}
        if after:
            x, _, z = after  
            after_set = {(x + dx, 0, z + dz) for dx in xrange(-pad, pad + 1) for dz in xrange(-pad, pad + 1)}
        
        for sector in after_set - before_set:
            self.show_sector(sector)
        for sector in before_set - after_set:
            self.hide_sector(sector)
    
    def show_sector(self, sector):
        """Affiche un secteur."""
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.enqueue(self.show_block, position)
    
    def hide_sector(self, sector):
        """Cache un secteur."""
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.enqueue(self.hide_block, position)
    
    def get_other_cubes(self):
        """Obtient tous les cubes des autres joueurs."""
        return list(self.other_players.values())


def block_texture_data(block_type):
    """Retourne les coordonnées de texture pour un type de bloc."""
    def tex_coord_4x3(x, y):
        m_x, m_y = 1.0 / 4.0, 1.0 / 4.0
        dx, dy = x * m_x, y * m_y
        return [dx, dy, dx + m_x, dy, dx + m_x, dy + m_y, dx, dy + m_y]
    
    textures = {
        BlockType.GRASS: tex_coord_4x3(1, 0) + tex_coord_4x3(0, 0) * 5,
        BlockType.SAND: tex_coord_4x3(1, 1) * 6,
        BlockType.BRICK: tex_coord_4x3(2, 0) * 6,
        BlockType.STONE: tex_coord_4x3(2, 1) * 6,
        BlockType.WOOD: tex_coord_4x3(3, 1) * 6,
        BlockType.LEAF: tex_coord_4x3(3, 0) * 6,
        BlockType.WATER: tex_coord_4x3(0, 2) * 6,
    }
    return textures.get(block_type, tex_coord_4x3(0, 0) * 6)


class MinecraftWindow(pyglet.window.Window):
    """Fenêtre de jeu principale avec interface améliorée."""
    
    def __init__(self, **kwargs):
        # Configuration de la fenêtre
        width, height = config.get_window_size()
        
        super(MinecraftWindow, self).__init__(
            width=width, 
            height=height,
            caption='Minecraft Client Français - Par Assistant IA',
            resizable=True,
            vsync=config.get("graphics", "vsync", True)
        )
        
        # État du jeu
        self.exclusive = False
        self.flying = False
        self.crouch = False
        self.sprinting = False
        self.jumping = False
        
        # Position et rotation du joueur
        spawn_pos = config.get("player", "preferred_spawn", [30, 50, 80])
        self.position = tuple(spawn_pos)
        self.rotation = (0, 0)
        
        # Mouvement
        self.strafe = [0, 0]
        self.dy = 0
        self.on_ground = False  # For server-side physics
        self.collision_types = {"top": False, "bottom": False, "right": False, "left": False}
        
        # FOV et vitesses
        self.fov_offset = 0
        self.movement_speed = config.get("player", "movement_speed", 5.0)
        self.jump_speed = config.get("player", "jump_speed", 8.0)
        self.flying_speed = config.get("player", "flying_speed", 15.0)
        
        # Inventaire
        self.inventory = [BlockType.BRICK, BlockType.GRASS, BlockType.SAND, BlockType.STONE]
        self.block = self.inventory[0]
        
        # Touches de mouvement configurables
        self.movement_keys = config.get_movement_keys()
        self.num_keys = [key._1, key._2, key._3, key._4, key._5]
        
        # Modèle et réseau
        self.model = EnhancedClientModel()
        self.network = AdvancedNetworkClient(self)
        
        # Interface utilisateur
        self.show_debug = config.get("interface", "show_debug_info", True)
        self.messages = []
        self.last_message_time = 0
        
        # Labels pour l'interface
        self.setup_ui()
        
        # Timing
        self.sector = None
        self._last_position_update = 0
        self._position_update_interval = 1.0 / 20  # 20 FPS pour les updates de position
        
        # Initialisation
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
        self.network.start_connection()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        # Labels
        self.label = pyglet.text.Label(
            '', font_name='Arial', font_size=12,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(255, 255, 255, 255)
        )
        
        self.message_label = pyglet.text.Label(
            '', font_name='Arial', font_size=14,
            x=self.width // 2, y=self.height - 50, anchor_x='center', anchor_y='top',
            color=(255, 255, 0, 255)
        )
        
        # Viseur simple
        self.setup_crosshair()
    
    def setup_crosshair(self):
        """Configure le viseur (crosshair) au centre de l'écran."""
        x, y, n = self.width // 2, self.height // 2, 10
        try:
            color = config.get("interface", "crosshair_color", [255, 255, 255])
            self.reticle = pyglet.graphics.vertex_list(4,
                ('v2f/static', (float(x - n), float(y), float(x + n), float(y), float(x), float(y - n), float(x), float(y + n))),
                ('c3B/static', color * 4)
            )
        except:
            # Fallback without color if there's an issue
            self.reticle = pyglet.graphics.vertex_list(4,
                ('v2f/static', (float(x - n), float(y), float(x + n), float(y), float(x), float(y - n), float(x), float(y + n)))
            )
    
    def show_message(self, text: str, duration: float = 3.0):
        """Affiche un message temporaire."""
        self.messages.append((text, time.time() + duration))
    
    def update_message_display(self):
        """Met à jour l'affichage des messages."""
        current_time = time.time()
        self.messages = [(text, exp_time) for text, exp_time in self.messages if exp_time > current_time]
        
        self.message_label.text = self.messages[-1][0] if self.messages else ""
    
    def set_exclusive_mouse(self, exclusive):
        """Configure la capture exclusive de la souris."""
        super(MinecraftWindow, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
    
    def get_sight_vector(self):
        """Calcule le vecteur de visée."""
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)
    
    def get_motion_vector(self):
        """Calcule le vecteur de mouvement."""
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
                    dy -= 0.2 * math.sin(y_angle)
                if self.strafe[0] < 0:
                    dy += 0.2 * math.sin(y_angle)
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
        
        # Envoie la position au serveur
        current_time = time.time()
        if current_time - self._last_position_update > self._position_update_interval:
            self._send_position_update()
            self._last_position_update = current_time
        
        # Met à jour l'interface
        self.update_ui()
        self.update_message_display()
    
    def _update_physics(self, dt):
        """Met à jour la physique du joueur."""
        dt = min(dt, 0.2)
        
        # Vitesse selon le mode
        if self.flying:
            speed = self.flying_speed
        elif self.sprinting:
            speed = self.movement_speed * 1.5
        elif self.crouch:
            speed = self.movement_speed * 0.5
        else:
            speed = self.movement_speed
        
        # Saut - seulement possible quand on est sur le sol (collision_types["top"] = True)
        if self.jumping and not self.flying:
            if self.collision_types["top"]:
                self.dy = self.jump_speed
        
        # Distance parcourue
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        
        # Gravité (reduced since server handles physics)
        if not self.flying:
            # Apply minimal client-side gravity for responsiveness
            self.dy -= dt * (GRAVITY * 0.3)  # Reduced to 30% of original
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        
        # Collisions
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)
    
    def collide(self, position, height):
        """Gère les collisions avec les blocs."""
        pad = 0.25
        p = list(position)
        np = normalize(position)
        self.collision_types = {"top": False, "bottom": False, "right": False, "left": False}
        
        # Collision avec les blocs
        for face in FACES:
            for i in xrange(3):
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                # FIX: Allow downward collision detection even with small d values
                # This enables proper ground collision detection
                if d < pad and not (face == (0, -1, 0) and i == 1):
                    continue
                    
                for dy in xrange(height):
                    op = list(np)
                    op[1] -= dy
                    
                    # COLLISION FIX: For downward collision, check the block the player is standing on
                    if face == (0, -1, 0) and i == 1:
                        # For downward collision, check blocks the player might be colliding with
                        # This prevents falling through blocks during rapid movement
                        floor_y = int(p[1]) - dy
                        if p[1] < 0:
                            # If player is underground, check blocks at ground level and above
                            # This ensures underground players get pushed back to surface
                            for check_y in range(max(floor_y, -2), 2):
                                test_op = list(np)
                                test_op[0] = op[0]
                                test_op[1] = check_y
                                test_op[2] = op[2] 
                                if tuple(test_op) in self.model.world:
                                    op[1] = check_y
                                    break
                            else:
                                op[1] = floor_y
                        else:
                            op[1] = floor_y
                    else:
                        op[i] += face[i]
                    
                    if tuple(op) not in self.model.world:
                        continue
                        
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0):
                        self.collision_types["top"] = True
                        self.dy = 0
                    if face == (0, 1, 0):
                        self.collision_types["bottom"] = True
                        self.dy = 0
                    break
        
        # Collision avec les autres joueurs
        player_collision = check_player_collision_with_direction(tuple(p), 0.4, self.model.get_other_cubes())
        if player_collision['collision']:
            # Si collision "top" (joueur sur un autre joueur), arrêter la gravité
            if player_collision['top']:
                self.collision_types["top"] = True
                self.dy = 0
            # Si collision "bottom" (autre joueur sur le joueur actuel), arrêter le mouvement vers le haut  
            elif player_collision['bottom']:
                self.collision_types["bottom"] = True
                self.dy = 0
            # Pour toute collision avec un joueur, empêcher le mouvement
            return position
            
        return tuple(p)
    
    def _send_position_update(self):
        """Envoie la mise à jour de position au serveur."""
        if self.network.connected:
            # Send absolute position instead of delta
            move_msg = create_player_move_message(self.position, self.rotation)
            self.network.send_message(move_msg)
    
    def update_ui(self):
        """Met à jour l'interface utilisateur."""
        if not self.show_debug:
            self.label.text = ""
            return
        
        stats = self.network.get_connection_stats()
        x, y, z = self.position
        visible_blocks = len(self.model.shown)
        total_blocks = len(self.model.world)
        connection_status = "Connecté" if stats["connected"] else "Déconnecté"
        
        # Indicateurs d'état
        status_indicators = []
        if self.flying: status_indicators.append("Vol")
        if self.sprinting: status_indicators.append("Course")
        if self.crouch: status_indicators.append("Accroupi")
        
        debug_text = f"""Minecraft Client Français v1.0
Position: {x:.1f}, {y:.1f}, {z:.1f}
Blocs: {visible_blocks}/{total_blocks}
Statut: {connection_status}"""
        
        if stats["connected"]:
            debug_text += f" | Ping: {stats['ping_ms']}ms"
        
        if status_indicators:
            debug_text += f"\nÉtat: {', '.join(status_indicators)}"
        
        debug_text += f"\nJoueurs: {len(self.model.other_players) + 1}"
        debug_text += f"\nBloc: {self.block}"
        
        self.label.text = debug_text
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Gère les clics de souris."""
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            
            if (button == mouse.RIGHT) or ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # Placer un bloc
                if previous:
                    place_msg = create_block_place_message(previous, self.block)
                    self.network.send_message(place_msg)
            
            elif button == mouse.LEFT and block:
                # Détruire un bloc
                destroy_msg = create_block_destroy_message(block)
                self.network.send_message(destroy_msg)
        else:
            self.set_exclusive_mouse(True)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Gère le mouvement de la souris."""
        if self.exclusive:
            sensitivity = config.get("controls", "mouse_sensitivity", 0.15)
            invert_y = config.get("controls", "invert_mouse_y", False)
            
            x_rot, y_rot = self.rotation
            x_rot += dx * sensitivity
            y_rot += dy * sensitivity * (-1 if invert_y else 1)
            y_rot = max(-90, min(90, y_rot))
            self.rotation = (x_rot, y_rot)
    
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
            status = config.get_localized_text("flying") if self.flying else "Vol désactivé"
            self.show_message(status)
        elif symbol == key.F3:
            self.show_debug = not self.show_debug
        elif symbol == key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
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
    
    def on_close(self):
        """Gère la fermeture de la fenêtre."""
        print("Fermeture du client...")
        self.network.disconnect()
        config.save_config()
        super(MinecraftWindow, self).on_close()
    
    def set_3d(self):
        """Configure OpenGL pour le rendu 3D."""
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        fov = config.get("graphics", "fov", PLAYER_FOV) + self.fov_offset
        gluPerspective(fov, width / float(height), 0.1, config.get("graphics", "render_distance", 60.0))
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        
        # Position camera to align with player cube
        # The cube is rendered at y + size, so camera should be positioned relative to that
        if self.crouch:
            # When crouching, position slightly lower within the cube
            cube_center_y = y + 0.4  # Cube center (y + size)
            camera_y = cube_center_y - 0.2  # Slightly lower when crouching
            glTranslatef(-x, -camera_y, -z)
        else:
            # Position camera at the center/top of the player cube for normal stance
            # This aligns the camera view with where the cube is actually rendered
            cube_center_y = y + 0.4  # Cube center matches get_render_position logic
            glTranslatef(-x, -cube_center_y, -z)
    
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
        
        # Rendu des joueurs
        self.draw_players()  # Affiche les autres joueurs comme des cubes colorés
        self.draw_player_labels()  # Affiche les noms des joueurs
        
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
    
    def draw_players(self):
        """Dessine tous les cubes des joueurs."""
        for player_id, player in self.model.other_players.items():
            if isinstance(player, PlayerState):
                color = self._get_player_color(player_id)
                x, y, z = player.get_render_position()
                vertex_data = cube_vertices(x, y, z, player.size)
                
                glColor3d(*color)
                pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
    
    def draw_player_labels(self):
        """Dessine les noms des joueurs."""
        width, height = self.get_size()
        self.set_2d()
        
        for player_id, player in self.model.other_players.items():
            if hasattr(player, 'name') and player.name:
                x, y, z = player.position
                player_distance = math.sqrt((x - self.position[0])**2 + 
                                          (y - self.position[1])**2 + 
                                          (z - self.position[2])**2)
                
                if player_distance < 20.0:
                    dx = x - self.position[0]
                    dz = z - self.position[2]
                    
                    screen_x = width // 2 + int(dx * 50 / max(abs(dz), 1))
                    screen_y = height // 2 + int((y - self.position[1]) * 50 / max(abs(dz), 1))
                    
                    if (0 <= screen_x <= width and 0 <= screen_y <= height and dz > 0):
                        label = pyglet.text.Label(
                            player.name, font_size=12, x=screen_x, y=screen_y,
                            anchor_x='center', anchor_y='center', color=(255, 255, 255, 255)
                        )
                        label.draw()
        
        # Restaurer le rendu 3D
        self.set_3d()
    
    def _get_player_color(self, player_id):
        """Obtient ou crée une couleur unique pour un joueur."""
        if not hasattr(self, '_player_colors'):
            self._player_colors = {}
        
        if player_id not in self._player_colors:
            import hashlib
            hash_hex = hashlib.md5(player_id.encode()).hexdigest()
            
            r = int(hash_hex[0:2], 16) / 255.0
            g = int(hash_hex[2:4], 16) / 255.0  
            b = int(hash_hex[4:6], 16) / 255.0
            
            # Ensure brightness
            brightness = (r + g + b) / 3
            if brightness < 0.5:
                factor = 0.7 / brightness
                r, g, b = min(1.0, r * factor), min(1.0, g * factor), min(1.0, b * factor)
            
            self._player_colors[player_id] = (r, g, b)
            
        return self._player_colors[player_id]
    
    def draw_ui(self):
        """Dessine l'interface utilisateur."""
        # Labels de debug
        if self.show_debug:
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
    parser = argparse.ArgumentParser(description="Client Minecraft amélioré avec support français")
    parser.add_argument('--server', '-s', help='Adresse du serveur (format: host:port)')
    parser.add_argument('--config', '-c', default='client_config.json', help='Fichier de configuration')
    parser.add_argument('--fullscreen', '-f', action='store_true', help='Démarrer en plein écran')
    parser.add_argument('--debug', '-d', action='store_true', help='Activer le mode debug')
    parser.add_argument('--lang', choices=['fr', 'en'], default='fr', help='Langue de l\'interface')
    return parser.parse_args()


def main():
    """Point d'entrée principal du client."""
    print("🎮 Client Minecraft Français - Démarrage...")
    args = parse_args()
    
    # Charge la configuration si différente
    if args.config != 'client_config.json':
        global config
        from client_config import ClientConfig
        config = ClientConfig(args.config)
    
    # Applique les arguments
    if args.server:
        try:
            host, port = (args.server.split(':', 1) if ':' in args.server else (args.server, 8765))
            config.set("server", "host", host)
            if ':' in args.server:
                config.set("server", "port", int(port))
        except ValueError:
            print(f"⚠️  Format serveur invalide: {args.server}")
            return 1
    
    # Applique les autres options
    for key, setting in [("fullscreen", ("graphics", "fullscreen")), 
                        ("debug", ("interface", "show_debug_info")), 
                        ("lang", ("interface", "language"))]:
        if getattr(args, key):
            config.set(setting[0], setting[1], getattr(args, key))
    
    print(f"🌐 Serveur: {config.get_server_url()}")
    print(f"⌨️  Layout: {'AZERTY' if config.is_azerty_layout() else 'QWERTY'}")
    
    try:
        window = MinecraftWindow()
        if config.get("graphics", "fullscreen", False):
            window.set_fullscreen(True)
        setup_opengl()
        window.show_message(config.get_localized_text("welcome"), 5.0)
        print("✅ Client démarré avec succès!")
        pyglet.app.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
