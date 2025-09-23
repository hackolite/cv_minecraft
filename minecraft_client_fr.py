#!/usr/bin/env python3
"""
Client Minecraft Minimal
========================

Client Minecraft simplifié utilisant Pyglet avec fonctionnalités de base.
"""

# Standard library imports
import sys, math, random, time, json, argparse, asyncio, threading
from collections import deque

# Third-party imports  
import pyglet, websockets
from pyglet.gl import *
from pyglet.window import key, mouse

# Project imports
from protocol import *
from client_config import config
from minecraft_physics import MinecraftCollisionDetector, MinecraftPhysics, PLAYER_HEIGHT, GRAVITY, JUMP_VELOCITY

# Game constants  
TICKS_PER_SEC = 60
WALKING_SPEED = 5
FLYING_SPEED = 15
PLAYER_FOV = 70.0

# Utility functions
def normalize(position):
    """Normalise la position aux coordonnées de bloc."""
    return tuple(int(round(x)) for x in position)

def sectorize(position):
    """Retourne le secteur contenant la position donnée."""
    x, y, z = normalize(position)
    return (x // 16, 0, z // 16)

def cube_vertices(x, y, z, n):
    """Retourne les vertices d'un cube."""
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom  
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]

class NetworkClient:
    """Client réseau minimal."""
    
    def __init__(self, window):
        self.window = window
        self.running = False
    
    def start_connection(self):
        """Démarre la connexion réseau."""
        self.running = True
        threading.Thread(target=self._run_network_thread, daemon=True).start()
    
    def _run_network_thread(self):
        """Thread réseau."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._connect_to_server())
    
    async def _connect_to_server(self):
        """Se connecte au serveur."""
        try:
            uri = config.get_server_url()
            async with websockets.connect(uri) as websocket:
                # Envoi du message de connexion
                join_msg = {"type": "player_join", "data": {"name": "Player"}}
                await websocket.send(json.dumps(join_msg))
                
                # Écoute des messages
                async for message in websocket:
                    data = json.loads(message)
                    self._handle_message(data)
        except Exception as e:
            print(f"Erreur réseau: {e}")
    
    def _handle_message(self, data):
        """Traite un message du serveur."""
        if data["type"] == "world_init":
            spawn = data.get("spawn_position", [30, 50, 80])
            self.window.position = tuple(spawn)
        elif data["type"] == "world_chunk":
            chunk_data = data["data"]
            for pos_str, block_type in chunk_data.get("blocks", {}).items():
                pos = tuple(map(int, pos_str.split(",")))
                self.window.model.add_block(pos, block_type)
    
    def send_position_update(self, position):
        """Envoie une mise à jour de position."""
        pass  # Simplifiée
    
    def disconnect(self):
        """Se déconnecte."""
        self.running = False

class EnhancedClientModel:
    """Modèle client minimal."""
    
    def __init__(self):
        self.world = {}
        self.shown = {}
        self.queue = deque()
    
    def add_block(self, position, block_type, immediate=True):
        """Ajoute un bloc."""
        self.world[position] = block_type
        if immediate:
            self.show_block(position)
    
    def remove_block(self, position, immediate=True):
        """Retire un bloc."""
        if position in self.world:
            del self.world[position]
            self.hide_block(position)
    
    def show_block(self, position, immediate=True):
        """Affiche un bloc."""
        if position in self.world and position not in self.shown:
            self.shown[position] = pyglet.graphics.vertex_list(24, ('v3f/static', cube_vertices(*position, 0.5)))
    
    def hide_block(self, position):
        """Cache un bloc."""
        if position in self.shown:
            self.shown[position].delete()
            del self.shown[position]
    
    def process_queue(self):
        """Traite la queue de rendu."""
        pass

class MinecraftWindow(pyglet.window.Window):
    """Fenêtre de jeu principale minimale."""
    
    def __init__(self):
        super(MinecraftWindow, self).__init__(
            width=1024, height=768,
            caption='Minecraft Client Minimal',
            resizable=True
        )
        
        # État du jeu
        self.exclusive = False
        self.flying = False
        self.position = (30, 50, 80)
        self.rotation = (0, 0)
        self.strafe = [0, 0]
        self.dy = 0
        
        # Vitesses
        self.movement_speed = 5.0
        self.flying_speed = 15.0
        
        # Inventaire
        self.inventory = [BlockType.BRICK, BlockType.GRASS, BlockType.SAND, BlockType.STONE]
        self.block = self.inventory[0]
        
        # Modèle et réseau
        from client import ClientModel
        self.model = ClientModel()
        self.network = NetworkClient(self)
        
        # Interface
        self.show_debug = True
        self.label = pyglet.text.Label(
            '', font_name='Arial', font_size=8,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 255)
        )
        
        # Configuration OpenGL
        self.setup_opengl()
        
        # Démarrage réseau
        self.network.start_connection()
        
        # Capture de souris
        pyglet.clock.schedule_interval(self.update, 1.0/TICKS_PER_SEC)
    
    def setup_opengl(self):
        """Configure OpenGL."""
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.5, 0.69, 1.0, 1)  # Couleur ciel
    
    def set_3d(self):
        """Configure la projection 3D."""
        width, height = self.get_size()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(PLAYER_FOV, width / float(height), 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)
    
    def set_2d(self):
        """Configure la projection 2D."""
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def on_draw(self):
        """Rendu."""
        self.clear()
        
        # Rendu 3D
        self.set_3d()
        glColor3d(1, 1, 1)
        for position in self.model.shown:
            self.model.shown[position].draw(GL_QUADS)
        
        # Rendu 2D
        self.set_2d()
        if self.show_debug:
            x, y, z = self.position
            self.label.text = f'X: {x:.1f} Y: {y:.1f} Z: {z:.1f} | Blocs: {len(self.model.world)}'
            self.label.draw()
    
    def update(self, dt):
        """Mise à jour."""
        self.model.process_queue()
        
        # Physique simple
        d = dt * self.movement_speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        
        if self.flying:
            x, y, z = self.position
            self.position = (x + dx, y + dy, z + dz)
        else:
            # Gravité basique
            self.dy -= GRAVITY * dt
            x, y, z = self.position
            new_y = y + self.dy * dt
            self.position = (x + dx, new_y, z + dz)
    
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
                    dy *= -1
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dx = math.cos(x_angle)
                dy = 0.0
                dz = math.sin(x_angle)
        else:
            dx = dy = dz = 0.0
        
        return (dx, dy, dz)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Mouvement souris."""
        if self.exclusive:
            sensitivity = 0.15
            x_rot, y_rot = self.rotation
            x_rot += dx * sensitivity
            y_rot += dy * sensitivity
            y_rot = max(-90, min(90, y_rot))
            self.rotation = (x_rot, y_rot)
    
    def on_key_press(self, symbol, modifiers):
        """Touches pressées."""
        if symbol == key.Z:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.Q:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.flying:
                self.strafe[1] += 1
            else:
                self.dy = 8.0  # Saut
        elif symbol == key.LSHIFT:
            if self.flying:
                self.strafe[1] -= 1
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol == key.F3:
            self.show_debug = not self.show_debug
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol in [key._1, key._2, key._3, key._4]:
            index = symbol - key._1
            if index < len(self.inventory):
                self.block = self.inventory[index]
    
    def on_key_release(self, symbol, modifiers):
        """Touches relâchées."""
        if symbol == key.Z:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.Q:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
        elif symbol == key.SPACE and self.flying:
            self.strafe[1] -= 1
        elif symbol == key.LSHIFT and self.flying:
            self.strafe[1] += 1
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Clic souris."""
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if button == mouse.LEFT and block:
                self.model.remove_block(block)
            elif button == mouse.RIGHT and previous:
                self.model.add_block(previous, self.block)
        else:
            self.set_exclusive_mouse(True)
    
    def get_sight_vector(self):
        """Vecteur de visée."""
        x, y = self.rotation
        x, y = math.radians(x), math.radians(y)
        dx = math.cos(x) * math.cos(y)
        dy = math.sin(y)
        dz = math.sin(x) * math.cos(y)
        return (dx, dy, dz)
    
    def hit_test(self, position, vector, max_distance=8):
        """Test de collision pour visée."""
        # Simplifié
        return None, None
    
    def set_exclusive_mouse(self, exclusive):
        """Configure la capture de souris."""
        super(MinecraftWindow, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
    
    def on_close(self):
        """Fermeture."""
        self.network.disconnect()
        super(MinecraftWindow, self).on_close()

def setup_opengl():
    """Configuration OpenGL globale."""
    glEnable(GL_DEPTH_TEST)

def main():
    """Point d'entrée principal."""
    print("🎮 Client Minecraft Minimal - Démarrage...")
    
    try:
        window = MinecraftWindow()
        setup_opengl()
        print("✅ Client démarré avec succès!")
        pyglet.app.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())