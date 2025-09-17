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

from __future__ import division

import sys
import math
import random
import time
import asyncio
import threading
import websockets
import json
import argparse
from collections import deque
from typing import Optional, Tuple, Dict, Any

import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

# Import missing GL constants if not available from pyglet
try:
    GL_FOG
except NameError:
    try:
        from OpenGL.GL import (
            GL_FOG, GL_FOG_COLOR, GL_FOG_HINT, GL_DONT_CARE,
            GL_FOG_MODE, GL_LINEAR, GL_FOG_START, GL_FOG_END,
            GL_QUADS, GL_DEPTH_TEST, GL_PROJECTION, GL_MODELVIEW,
            GL_FRONT_AND_BACK, GL_LINE, GL_FILL, GL_LINES,
            GL_CULL_FACE, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
            GL_NEAREST, GL_TEXTURE_MAG_FILTER, GLfloat
        )
    except ImportError:
        raise ImportError("OpenGL constants not available. Please install PyOpenGL: pip install PyOpenGL")

try:
    from pyglet.graphics import get_default_shader
except ImportError:
    get_default_shader = None

# Import des modules du projet
from protocol import *
from client_config import config

# Constantes du jeu
TICKS_PER_SEC = 60
WALKING_SPEED = 5
FLYING_SPEED = 15
JUMP_SPEED = 8.0
TERMINAL_VELOCITY = 50
PLAYER_HEIGHT = 2
GRAVITY = 20.0
PLAYER_FOV = 70.0
SPRINT_FOV = 10.0

# Autres constantes depuis l'original
TEXTURE_PATH = 'texture.png'

# Compatibility for xrange in Python 3
try:
    xrange
except NameError:
    xrange = range

# Utilitaires
FACES = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]

def normalize(position):
    """Normalize position to block coordinates."""
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

def sectorize(position):
    """Return sector that contains the given position."""
    x, y, z = normalize(position)
    x, y, z = x // 16, y // 16, z // 16
    return (x, 0, z)

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

class AdvancedNetworkClient:
    """Client réseau amélioré avec reconnexion automatique et gestion d'erreurs robuste."""
    
    def __init__(self, window, server_url: str = None):
        self.window = window
        self.server_url = server_url or config.get_server_url()
        self.websocket = None
        self.connected = False
        self.loop = None
        self.thread = None
        self.player_id = None
        self.connection_attempts = 0
        self.max_connection_attempts = config.get("server", "max_connection_attempts", 5)
        self.reconnect_delay = 5
        self.last_ping_time = 0
        self.ping_ms = 0
        
        # Statistiques de connexion
        self.messages_sent = 0
        self.messages_received = 0
        self.connection_time = 0
        
    def start_connection(self):
        """Démarre la connexion réseau dans un thread séparé."""
        if self.thread and self.thread.is_alive():
            return
            
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
            print(f"Erreur dans le thread réseau: {e}")
        finally:
            self.loop.close()
    
    async def _connection_manager(self):
        """Gestionnaire de connexion avec reconnexion automatique."""
        while True:
            try:
                await self._connect_to_server()
                # Si on arrive ici, la connexion s'est fermée normalement
                break
            except Exception as e:
                self.connected = False
                self.connection_attempts += 1
                
                if self.connection_attempts >= self.max_connection_attempts:
                    print(f"Nombre maximum de tentatives de connexion atteint: {self.max_connection_attempts}")
                    break
                
                print(f"Tentative de connexion {self.connection_attempts}/{self.max_connection_attempts} échouée: {e}")
                
                if config.get("server", "auto_reconnect", True):
                    print(f"Reconnexion dans {self.reconnect_delay} secondes...")
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 1.5, 30)  # Backoff exponentiel
                else:
                    break
    
    async def _connect_to_server(self):
        """Se connecte au serveur et gère les messages."""
        timeout = config.get("server", "connection_timeout", 10)
        
        try:
            print(f"Connexion à {self.server_url}...")
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.server_url), 
                timeout=timeout
            )
            
            self.connected = True
            self.connection_time = time.time()
            self.connection_attempts = 0
            self.reconnect_delay = 5
            
            print(config.get_localized_text("connected"))
            
            # Envoie le message de connexion
            player_name = config.get("player", "name", "Joueur")
            join_msg = create_player_join_message(player_name)
            await self.websocket.send(join_msg.to_json())
            self.messages_sent += 1
            
            # Démarre le ping
            ping_task = asyncio.create_task(self._ping_loop())
            
            # Écoute les messages
            try:
                async for message_str in self.websocket:
                    try:
                        message = Message.from_json(message_str)
                        self.messages_received += 1
                        
                        # Programme la gestion du message sur le thread principal
                        pyglet.clock.schedule_once(
                            lambda dt, msg=message: self._handle_server_message(msg), 0
                        )
                    except Exception as e:
                        print(f"Erreur lors du parsing du message: {e}")
                        
            finally:
                ping_task.cancel()
                
        except asyncio.TimeoutError:
            raise Exception(f"Timeout de connexion après {timeout}s")
        except Exception as e:
            raise Exception(f"Erreur de connexion: {e}")
        finally:
            self.connected = False
            self.websocket = None
    
    async def _ping_loop(self):
        """Boucle de ping pour mesurer la latence."""
        while self.connected and self.websocket:
            try:
                self.last_ping_time = time.time()
                pong_waiter = await self.websocket.ping()
                await pong_waiter
                self.ping_ms = int((time.time() - self.last_ping_time) * 1000)
                await asyncio.sleep(5)  # Ping toutes les 5 secondes
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
                blocks = message.data.get("blocks", [])
                for block_data in blocks:
                    block_update = BlockUpdate.from_dict(block_data)
                    position = block_update.position
                    
                    if block_update.block_type == BlockType.AIR:
                        self.window.model.remove_block(position)
                        self.window.show_message(config.get_localized_text("block_destroyed"))
                    else:
                        self.window.model.add_block(position, block_update.block_type)
                        self.window.show_message(config.get_localized_text("block_placed"))
                        
            elif message.type == MessageType.PLAYER_UPDATE:
                player_data = message.data
                player_id = player_data["id"]
                
                if player_id == self.player_id:
                    # Server is sending physics updates for our own player
                    self.window.position = tuple(player_data["position"])
                    self.window.dy = player_data["velocity"][1]  # Update Y velocity from server
                    self.window.on_ground = player_data.get("on_ground", False)
                else:
                    self.window.model.other_players[player_id] = PlayerState.from_dict(player_data)
                    
            elif message.type == MessageType.PLAYER_LIST:
                players = message.data.get("players", [])
                self.window.model.other_players = {}
                
                for player_data in players:
                    player = PlayerState.from_dict(player_data)
                    if player.id != self.player_id:
                        self.window.model.other_players[player.id] = player
                        
            elif message.type == MessageType.CHAT_BROADCAST:
                chat_text = message.data.get("text", "")
                self.window.show_message(f"[CHAT] {chat_text}")
                
            elif message.type == MessageType.ERROR:
                error_msg = message.data.get("message", "Erreur inconnue")
                self.window.show_message(f"{config.get_localized_text('server_error')}: {error_msg}")
                
        except Exception as e:
            print(f"Erreur lors de la gestion du message {message.type}: {e}")
    
    def send_message(self, message: Message):
        """Envoie un message au serveur."""
        if not self.connected or not self.websocket:
            return False
            
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send_message_async(message), self.loop
            )
            return True
        return False
    
    async def _send_message_async(self, message: Message):
        """Envoie un message de manière asynchrone."""
        if self.websocket:
            try:
                await self.websocket.send(message.to_json())
                self.messages_sent += 1
            except Exception as e:
                print(f"Erreur lors de l'envoi du message: {e}")
    
    def disconnect(self):
        """Se déconnecte du serveur."""
        if self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
        self.connected = False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de connexion."""
        uptime = time.time() - self.connection_time if self.connected else 0
        return {
            "connected": self.connected,
            "ping_ms": self.ping_ms,
            "uptime": uptime,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "server_url": self.server_url
        }


class EnhancedClientModel:
    """Modèle client amélioré avec gestion optimisée des blocs."""
    
    def __init__(self):
        # Batch pour le rendu groupé
        self.batch = pyglet.graphics.Batch()
        
        # Gestionnaire de texture
        try:
            self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())
        except Exception as e:
            print(f"Erreur lors du chargement de la texture: {e}")
            self.group = None
        
        # Données du monde
        self.world = {}
        self.shown = {}
        self._shown = {}
        self.sectors = {}
        self.queue = deque()
        
        # Autres joueurs
        self.other_players = {}
        
        # Informations du monde
        self.world_size = 128
        self.spawn_position = [30, 50, 80]
        
        # Cache pour optimisation
        self._block_cache = {}
        self._last_sector_update = 0
    
    def load_world_data(self, world_data):
        """Charge les données initiales du monde depuis le serveur."""
        self.world_size = world_data.get("world_size", 128)
        self.spawn_position = world_data.get("spawn_position", [30, 50, 80])
        print(f"Monde initialisé: taille {self.world_size}, spawn {self.spawn_position}")
    
    def load_world_chunk(self, chunk_data):
        """Charge un chunk de données du monde."""
        blocks = chunk_data.get("blocks", {})
        blocks_loaded = 0
        
        for pos_str, block_type in blocks.items():
            try:
                x, y, z = map(int, pos_str.split(','))
                position = (x, y, z)
                self.add_block(position, block_type, immediate=False)
                blocks_loaded += 1
            except ValueError:
                continue
        
        print(f"Chunk chargé: {blocks_loaded} blocs")
    
    def add_block(self, position, block_type, immediate=True):
        """Ajoute un bloc au monde."""
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        
        if immediate:
            if self.exposed(position):
                self.show_block(position)
        else:
            self.enqueue(self.show_block, position)
    
    def remove_block(self, position, immediate=True):
        """Retire un bloc du monde."""
        del self.world[position]
        self.hide_block(position)
        
        if immediate:
            for neighbor in self.neighbors(position):
                if neighbor in self.world and neighbor not in self.shown:
                    if self.exposed(neighbor):
                        self.show_block(neighbor)
        else:
            for neighbor in self.neighbors(position):
                self.enqueue(self.check_if_exposed, neighbor)
    
    def neighbors(self, position):
        """Retourne les voisins d'un bloc."""
        x, y, z = position
        for dx, dy, dz in FACES:
            yield (x + dx, y + dy, z + dz)
    
    def exposed(self, position):
        """Vérifie si un bloc est exposé (visible)."""
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
    
    def show_block(self, position, immediate=True):
        """Affiche un bloc."""
        block_type = self.world.get(position)
        if not block_type:
            return
            
        if position in self.shown:
            return
            
        if not self.group:
            return
            
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(block_texture_data(block_type))
        
        # Crée la liste de vertices pour le rendu
        try:
            self._shown[position] = self.batch.add(
                24, GL_QUADS, self.group,
                ('v3f/static', vertex_data),
                ('t2f/static', texture_data)
            )
            self.shown[position] = block_type
        except Exception as e:
            print(f"Erreur lors de l'affichage du bloc {position}: {e}")
    
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
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        
        for _ in xrange(max_distance * m):
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
        
        for dx in xrange(-pad, pad + 1):
            for dz in xrange(-pad, pad + 1):
                if before:
                    x, _, z = before
                    before_set.add((x + dx, 0, z + dz))
                if after:
                    x, _, z = after
                    after_set.add((x + dx, 0, z + dz))
        
        show = after_set - before_set
        hide = before_set - after_set
        
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
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
    
    def check_if_exposed(self, position):
        """Vérifie et affiche un bloc s'il est exposé."""
        if position in self.world and position not in self.shown:
            if self.exposed(position):
                self.show_block(position)


def block_texture_data(block_type):
    """Retourne les coordonnées de texture pour un type de bloc."""
    # Coordonnées de texture pour une grille 4x3 dans texture.png
    # Chaque texture fait 1/4 de la largeur et 1/3 de la hauteur totale
    def tex_coord_4x3(x, y):
        """Retourne les coordonnées d'une texture dans une grille 4x3."""
        m_x = 1.0 / 4.0  # 4 colonnes
        m_y = 1.0 / 3.0  # 3 rangées
        dx = x * m_x
        dy = y * m_y
        return [dx, dy, dx + m_x, dy, dx + m_x, dy + m_y, dx, dy + m_y]
    
    textures = {
        BlockType.GRASS: tex_coord_4x3(0, 0) * 6,  # Position (0,0) - coin supérieur gauche
        BlockType.SAND: tex_coord_4x3(1, 1) * 6,   # Position (1,1) - milieu centre-gauche
        BlockType.BRICK: tex_coord_4x3(2, 0) * 6,  # Position (2,0) - haut centre-droit
        BlockType.STONE: tex_coord_4x3(2, 1) * 6,  # Position (2,1) - milieu centre-droit
        BlockType.WOOD: tex_coord_4x3(3, 1) * 6,   # Position (3,1) - milieu droite
        BlockType.LEAF: tex_coord_4x3(3, 0) * 6,   # Position (3,0) - haut droite
        BlockType.WATER: tex_coord_4x3(0, 2) * 6,  # Position (0,2) - bas gauche
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
        # Label principal avec informations de debug
        self.label = pyglet.text.Label(
            '', font_name='Arial', font_size=12,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(255, 255, 255, 255)
        )
        
        # Label pour les messages
        self.message_label = pyglet.text.Label(
            '', font_name='Arial', font_size=14,
            x=self.width // 2, y=self.height - 50, anchor_x='center', anchor_y='top',
            color=(255, 255, 0, 255)
        )
        
        # Viseur
        self.setup_crosshair()
    
    def setup_crosshair(self):
        """Configure le viseur."""
        x, y = self.width // 2, self.height // 2
        n = 10
        color = config.get("interface", "crosshair_color", [255, 255, 255])
        
        try:
            self.reticle = pyglet.graphics.vertex_list(4,
                ('v2f/static', (float(x - n), float(y), float(x + n), float(y), 
                               float(x), float(y - n), float(x), float(y + n))),
                ('c3B/static', color * 4)
            )
        except:
            self.reticle = pyglet.graphics.vertex_list(4,
                ('v2f/static', (float(x - n), float(y), float(x + n), float(y),
                               float(x), float(y - n), float(x), float(y + n)))
            )
    
    def show_message(self, text: str, duration: float = 3.0):
        """Affiche un message temporaire."""
        self.messages.append((text, time.time() + duration))
        self.update_message_display()
    
    def update_message_display(self):
        """Met à jour l'affichage des messages."""
        current_time = time.time()
        # Filtre les messages expirés
        self.messages = [(text, exp_time) for text, exp_time in self.messages if exp_time > current_time]
        
        if self.messages:
            # Affiche le message le plus récent
            self.message_label.text = self.messages[-1][0]
        else:
            self.message_label.text = ""
    
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
        
        for face in FACES:
            for i in xrange(3):
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                    
                for dy in xrange(height):
                    op = list(np)
                    op[1] -= dy
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
        
        # Statistiques de connexion
        stats = self.network.get_connection_stats()
        
        # Informations de position
        x, y, z = self.position
        
        # Statistiques de rendu
        visible_blocks = len(self.model.shown)
        total_blocks = len(self.model.world)
        
        # Statut de connexion
        connection_status = config.get_localized_text("connected" if stats["connected"] else "disconnected")
        
        # Indicateurs d'état
        status_indicators = []
        if self.flying:
            status_indicators.append(config.get_localized_text("flying"))
        if self.sprinting:
            status_indicators.append(config.get_localized_text("sprinting"))
        if self.crouch:
            status_indicators.append(config.get_localized_text("crouch"))
        
        # Format du texte de debug
        debug_text = f"""Minecraft Client Français v1.0
{config.get_localized_text("position")}: {x:.1f}, {y:.1f}, {z:.1f}
{config.get_localized_text("blocks_visible")}: {visible_blocks} | {config.get_localized_text("blocks_total")}: {total_blocks}
Statut: {connection_status}"""
        
        if stats["connected"]:
            debug_text += f" | {config.get_localized_text('ping')}: {stats['ping_ms']}ms"
        
        if status_indicators:
            debug_text += f"\nÉtat: {', '.join(status_indicators)}"
        
        debug_text += f"\nJoueurs en ligne: {len(self.model.other_players) + 1}"
        debug_text += f"\nBloc sélectionné: {self.block}"
        
        if config.get("interface", "show_coordinates", True):
            debug_text += f"\nSecteur: {sectorize(self.position)}"
        
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
                    if self.network.send_message(place_msg):
                        self.show_message(f"{config.get_localized_text('block_placed')}: {self.block}")
            
            elif button == mouse.LEFT and block:
                # Détruire un bloc
                destroy_msg = create_block_destroy_message(block)
                if self.network.send_message(destroy_msg):
                    self.show_message(config.get_localized_text("block_destroyed"))
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
        
        if self.crouch:
            glTranslatef(-x, -y + 0.2, -z)
        else:
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
    # Couleur de fond (ciel bleu)
    glClearColor(0.5, 0.69, 1.0, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    
    # Configuration du brouillard
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
    parser = argparse.ArgumentParser(
        description="Client Minecraft amélioré avec support français",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python3 minecraft_client_fr.py
  python3 minecraft_client_fr.py --server localhost:8765
  python3 minecraft_client_fr.py --config mon_config.json
  python3 minecraft_client_fr.py --server 192.168.1.100:8765 --fullscreen
        """
    )
    
    parser.add_argument(
        '--server', '-s',
        default=None,
        help='Adresse du serveur (format: host:port, défaut: localhost:8765)'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='client_config.json',
        help='Fichier de configuration (défaut: client_config.json)'
    )
    
    parser.add_argument(
        '--fullscreen', '-f',
        action='store_true',
        help='Démarrer en plein écran'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Activer le mode debug'
    )
    
    parser.add_argument(
        '--lang',
        choices=['fr', 'en'],
        default='fr',
        help='Langue de l\'interface (défaut: fr)'
    )
    
    return parser.parse_args()


def main():
    """Point d'entrée principal du client."""
    print("🎮 Client Minecraft Français - Démarrage...")
    print("📡 Utilise Pyglet pour le rendu et WebSocket pour le réseau")
    print("🇫🇷 Interface en français avec support AZERTY")
    print()
    
    # Parse les arguments
    args = parse_args()
    
    # Charge la configuration
    if args.config != 'client_config.json':
        global config
        from client_config import ClientConfig
        config = ClientConfig(args.config)
    
    # Applique les paramètres des arguments
    if args.server:
        try:
            if ':' in args.server:
                host, port = args.server.split(':', 1)
                config.set("server", "host", host)
                config.set("server", "port", int(port))
            else:
                config.set("server", "host", args.server)
        except ValueError:
            print(f"⚠️  Format d'adresse serveur invalide: {args.server}")
            print("   Format attendu: host:port (exemple: localhost:8765)")
            return 1
    
    if args.fullscreen:
        config.set("graphics", "fullscreen", True)
    
    if args.debug:
        config.set("interface", "show_debug_info", True)
    
    if args.lang:
        config.set("interface", "language", args.lang)
    
    # Affiche la configuration
    server_url = config.get_server_url()
    layout = "AZERTY" if config.is_azerty_layout() else "QWERTY"
    lang = config.get("interface", "language", "fr").upper()
    
    print(f"🌐 Serveur: {server_url}")
    print(f"⌨️  Layout clavier: {layout}")
    print(f"🗣️  Langue: {lang}")
    print(f"📁 Configuration: {config.config_file}")
    print()
    
    # Affiche les contrôles
    print("🎮 Contrôles:")
    keys = config.get_movement_keys()
    print(f"   {keys['forward']}/{keys['left']}/{keys['backward']}/{keys['right']} - Mouvement")
    print("   Espace - Saut")
    print("   Maj - S'accroupir")
    print("   R - Courir")
    print("   Tab - Voler")
    print("   F3 - Debug")
    print("   F11 - Plein écran")
    print("   Échap - Libérer souris")
    print("   1-5 - Sélection de bloc")
    print()
    
    try:
        # Crée la fenêtre
        window = MinecraftWindow()
        
        if config.get("graphics", "fullscreen", False):
            window.set_fullscreen(True)
        
        # Configure OpenGL
        setup_opengl()
        
        # Message de bienvenue
        welcome_msg = config.get_localized_text("welcome")
        controls_msg = config.get_localized_text("controls_help")
        window.show_message(f"{welcome_msg}\n{controls_msg}", 5.0)
        
        print("✅ Client démarré avec succès!")
        print("💡 Utilisez F3 pour les informations de debug")
        print("🚪 Fermez la fenêtre ou Ctrl+C pour quitter")
        print()
        
        # Lance la boucle principale
        pyglet.app.run()
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du client: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("👋 Client fermé proprement")
    return 0


if __name__ == "__main__":
    sys.exit(main())