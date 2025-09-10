#!/usr/bin/env python3
"""
Client Minecraft-like en Python avec Panda3D
Interface 3D et communication WebSocket avec le serveur
"""

from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import *
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
import asyncio
import websockets
import json
import threading
import queue
import time
from typing import Dict, List
import logging
import sys

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinecraftClient(ShowBase):
    def __init__(self, server_host="localhost", server_port=8765):
        ShowBase.__init__(self)
        
        self.server_host = server_host
        self.server_port = server_port
        self.websocket = None
        self.player_id = None
        self.player_name = "Joueur"
        
        # Files pour la communication entre threads
        self.message_queue = queue.Queue()
        self.send_queue = queue.Queue()
        
        # Stockage des entités du jeu
        self.world_blocks: Dict[tuple, NodePath] = {}
        self.other_players: Dict[str, NodePath] = {}
        
        # Types de blocs et leurs couleurs
        self.block_types = {
            "grass": (0, 0.8, 0, 1),      # vert
            "stone": (0.5, 0.5, 0.5, 1),  # gris
            "wood": (0.6, 0.3, 0, 1),     # marron
            "dirt": (0.4, 0.2, 0, 1),     # marron foncé
            "sand": (1, 1, 0, 1),         # jaune
            "water": (0, 0, 1, 1)         # bleu
        }
        
        self.current_block_type = "grass"
        
        # Variables de jeu
        self.connected = False
        self.last_position = (0, 0, 0)
        self.position_update_timer = 0
        
        # Variables pour gérer les clics souris
        self.click_cooldown = 0.2  # Délai minimum entre les clics (en secondes)
        self.last_click_time = 0
        
        # Interface
        self.chat_messages = []
        self.chat_visible = False
        
        # Variables de mouvement
        self.movement_speed = 20.0
        self.mouse_sensitivity = 1.0  # Réduit de 50.0 à 1.0 pour moins de sensibilité
        self.gravity = -20.0
        self.jump_force = 10.0
        self.velocity_y = 0
        self.is_grounded = False
        
        # Variables pour le mouvement de la souris
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_initialized = False
        
        # Touches pressées
        self.key_map = {
            "forward": False,
            "backward": False, 
            "left": False,
            "right": False,
            "jump": False
        }
        
        self.setup_panda3d()
        
    def setup_panda3d(self):
        """Initialise Panda3D et la scène 3D"""
        # Configuration de la fenêtre
        props = WindowProperties()
        props.setTitle("Minecraft-like Client (Panda3D)")
        base.win.requestProperties(props)
        
        # Désactiver la souris par défaut de Panda3D
        self.disableMouse()
        
        # Configurer la caméra pour vue à la première personne
        self.camera.setPos(0, 0, 10)
        self.camera.setHpr(0, 0, 0)
        
        # Configuration de l'éclairage
        self.render.setShaderAuto()
        
        # Lumière directionnelle
        dlight = DirectionalLight('dlight')
        dlight.setDirection(Vec3(1, -1, -1))
        dlnp = self.render.attachNewNode(dlight)
        self.render.setLight(dlnp)
        
        # Lumière ambiante
        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        # Configuration des contrôles
        self.setup_controls()
        
        # Interface utilisateur
        self.setup_ui()
        
        # Démarrer les tâches
        self.taskMgr.add(self.update_game, "update_game")
        self.taskMgr.add(self.update_movement, "update_movement")
        
    def setup_controls(self):
        """Configure les contrôles clavier et souris"""
        # Contrôles clavier
        self.accept("z", self.set_key, ["forward", True])
        self.accept("z-up", self.set_key, ["forward", False])
        self.accept("s", self.set_key, ["backward", True])
        self.accept("s-up", self.set_key, ["backward", False])
        self.accept("q", self.set_key, ["left", True])
        self.accept("q-up", self.set_key, ["left", False])
        self.accept("d", self.set_key, ["right", True])
        self.accept("d-up", self.set_key, ["right", False])
        self.accept("space", self.set_key, ["jump", True])
        self.accept("space-up", self.set_key, ["jump", False])
        
        # Contrôles souris
        self.accept("mouse1", self.handle_left_click)
        self.accept("mouse3", self.handle_right_click)
        
        # Changement de blocs (touches 1-6)
        for i in range(1, 7):
            self.accept(str(i), self.change_block_type, [i - 1])
            
        # Chat et quitter
        self.accept("t", self.toggle_chat)
        self.accept("escape", sys.exit)
        
        # Capturer la souris
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.MRelative)
        base.win.requestProperties(props)
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Texte d'information
        self.info_text = OnscreenText(
            text="🎮 Minecraft-like (Panda3D)\n" +
                 "ZQSD: Déplacer | Espace: Sauter | Clic gauche: Détruire | Clic droit: Placer\n" +
                 "1-6: Changer bloc | T: Chat | ESC: Quitter",
            pos=(-1.3, 0.9),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        # Indicateur de bloc sélectionné
        self.block_indicator = OnscreenText(
            text=f"Bloc: {self.current_block_type.title()}",
            pos=(1.0, 0.9),
            scale=0.06,
            fg=self.block_types.get(self.current_block_type, (1, 1, 1, 1)),
            align=TextNode.ARight
        )
        
        # Statut de connexion
        self.connection_status = OnscreenText(
            text="Connexion...",
            pos=(-1.3, -0.9),
            scale=0.05,
            fg=(1, 0, 0, 1),
            align=TextNode.ALeft
        )
        
        # Zone de chat (initialement cachée)
        self.chat_frame = DirectFrame(
            frameColor=(0.2, 0.2, 0.2, 0.7),
            frameSize=(-1.5, 1.5, -0.8, -0.2),
            pos=(0, 0, 0)
        )
        self.chat_frame.hide()
        
        self.chat_text = OnscreenText(
            text='',
            parent=self.chat_frame,
            pos=(0, 0.1),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter
        )
        
    def set_key(self, key, value):
        """Définit l'état d'une touche"""
        self.key_map[key] = value
        
    def handle_left_click(self):
        """Gère le clic gauche (détruire bloc)"""
        current_time = time.time()
        if current_time - self.last_click_time > self.click_cooldown:
            self.handle_block_interaction("remove")
            self.last_click_time = current_time
            
    def handle_right_click(self):
        """Gère le clic droit (placer bloc)"""
        current_time = time.time()
        if current_time - self.last_click_time > self.click_cooldown:
            self.handle_block_interaction("place")
            self.last_click_time = current_time
            
    def update_movement(self, task):
        """Met à jour le mouvement du joueur"""
        dt = globalClock.getDt()
        
        # Récupérer la position actuelle de la caméra
        pos = self.camera.getPos()
        hpr = self.camera.getHpr()
        
        # Calculer la direction de mouvement
        move_vector = Vec3(0, 0, 0)
        
        if self.key_map["forward"]:
            move_vector.y += self.movement_speed * dt
        if self.key_map["backward"]:
            move_vector.y -= self.movement_speed * dt
        if self.key_map["left"]:
            move_vector.x -= self.movement_speed * dt
        if self.key_map["right"]:
            move_vector.x += self.movement_speed * dt
            
        # Appliquer la rotation de la caméra au mouvement
        if move_vector.length() > 0:
            # Transformer le vecteur de mouvement selon l'orientation de la caméra
            move_vector = self.camera.getRelativeVector(self.render, move_vector)
            move_vector.z = 0  # Pas de mouvement vertical avec les touches de direction
            
            # Appliquer le mouvement
            new_pos = pos + move_vector
            self.camera.setPos(new_pos)
            
        # Gestion de la gravité et du saut
        if self.key_map["jump"] and self.is_grounded:
            self.velocity_y = self.jump_force
            self.is_grounded = False
            
        # Appliquer la gravité
        self.velocity_y += self.gravity * dt
        
        # Appliquer le mouvement vertical
        new_y = pos.z + self.velocity_y * dt
        
        # Collision simple avec le sol (y=0)
        if new_y <= 0:
            new_y = 0
            self.velocity_y = 0
            self.is_grounded = True
        else:
            self.is_grounded = False
            
        self.camera.setZ(new_y)
        
        # Gestion de la souris pour regarder autour
        if base.mouseWatcherNode.hasMouse():
            mouse_x = base.mouseWatcherNode.getMouseX()
            mouse_y = base.mouseWatcherNode.getMouseY()
            
            # Initialiser la position de la souris au premier passage
            if not self.mouse_initialized:
                self.last_mouse_x = mouse_x
                self.last_mouse_y = mouse_y
                self.mouse_initialized = True
                return task.cont
            
            # Calculer le delta du mouvement de la souris
            delta_x = mouse_x - self.last_mouse_x
            delta_y = mouse_y - self.last_mouse_y
            
            # Mise à jour de la rotation de la caméra avec les deltas
            current_h = hpr.x - delta_x * self.mouse_sensitivity
            current_p = max(-90, min(90, hpr.y - delta_y * self.mouse_sensitivity))
            
            self.camera.setHpr(current_h, current_p, 0)
            
            # Stocker la position actuelle pour le prochain frame
            self.last_mouse_x = mouse_x
            self.last_mouse_y = mouse_y
            
            # Recentrer la souris si elle s'éloigne trop du centre pour éviter l'accumulation
            if abs(mouse_x) > 0.8 or abs(mouse_y) > 0.8:
                base.win.movePointer(0, int(base.win.getXSize() / 2), int(base.win.getYSize() / 2))
                self.last_mouse_x = 0
                self.last_mouse_y = 0
            
        return task.cont
        
    async def connect_to_server(self):
        """Se connecte au serveur WebSocket"""
        try:
            uri = f"ws://{self.server_host}:{self.server_port}"
            logger.info(f"Connexion au serveur {uri}...")
            
            self.websocket = await websockets.connect(uri)
            self.connected = True
            
            # Envoyer demande de connexion
            join_message = {
                "type": "join",
                "name": self.player_name
            }
            await self.websocket.send(json.dumps(join_message))
            logger.info("Demande de connexion envoyée")
            
            return True
            
        except ConnectionRefusedError:
            logger.error(f"Impossible de se connecter au serveur {self.server_host}:{self.server_port}")
            logger.error("Vérifiez que le serveur est démarré et accessible")
            return False
        except Exception as e:
            logger.error(f"Erreur connexion serveur: {e}")
            return False
            
    async def handle_server_messages(self):
        """Gère les messages reçus du serveur"""
        try:
            while self.connected and self.websocket:
                try:
                    message_data = await asyncio.wait_for(
                        self.websocket.recv(), timeout=1.0
                    )
                    message = json.loads(message_data)
                    self.message_queue.put(message)
                    
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connexion fermée par le serveur")
                    break
                    
        except Exception as e:
            logger.error(f"Erreur réception messages: {e}")
        finally:
            self.connected = False
            
    async def send_messages_to_server(self):
        """Envoie les messages en attente au serveur"""
        while self.connected and self.websocket:
            try:
                if not self.send_queue.empty():
                    message = self.send_queue.get_nowait()
                    await self.websocket.send(json.dumps(message))
                await asyncio.sleep(0.01)  # Éviter la surcharge CPU
            except Exception as e:
                logger.error(f"Erreur envoi message: {e}")
                break
                
    def process_server_messages(self):
        """Traite les messages du serveur (appelé depuis le thread principal)"""
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                msg_type = message.get("type")
                
                if msg_type == "init":
                    self.player_id = message.get("player_id")
                    self.load_world(message.get("world", []))
                    self.update_players(message.get("players", []))
                    
                    # Set initial player position from server data
                    players_data = message.get("players", [])
                    for player_data in players_data:
                        if player_data["id"] == self.player_id:
                            # Set our player's position to match server
                            self.camera.setPos(player_data["x"], player_data["y"], player_data["z"])
                            logger.info(f"Position initiale du joueur: ({player_data['x']}, {player_data['y']}, {player_data['z']})")
                            break
                    
                    self.connection_status.setText(f"Connecté (ID: {self.player_id[:8]})")
                    self.connection_status.setFg((0, 1, 0, 1))
                    
                elif msg_type == "players_update":
                    self.update_players(message.get("players", []))
                    
                elif msg_type == "world_update":
                    self.handle_world_update(message)
                    
                elif msg_type == "chat":
                    self.add_chat_message(
                        message.get("player_name"),
                        message.get("message")
                    )
                    
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Erreur traitement message: {e}")
                
    def load_world(self, world_data):
        """Charge le monde depuis les données serveur"""
        logger.info(f"Chargement du monde avec {len(world_data)} blocs...")
        
        # Supprimer les blocs existants
        for block in self.world_blocks.values():
            block.removeNode()
        self.world_blocks.clear()
        
        # Charger les nouveaux blocs
        blocks_created = 0
        for block_data in world_data:
            self.create_block(
                block_data["x"],
                block_data["y"], 
                block_data["z"],
                block_data["block_type"]
            )
            blocks_created += 1
            
        logger.info(f"✅ {blocks_created} blocs visuels créés et chargés")
            
    def create_block(self, x, y, z, block_type):
        """Crée un bloc visuel dans le monde"""
        try:
            # Créer un cube simple
            from panda3d.core import CardMaker
            cm = CardMaker("block")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            
            # Créer les 6 faces du cube
            block_node = self.render.attachNewNode("block")
            
            # Face avant
            face = block_node.attachNewNode(cm.generate())
            face.setPos(0, 0.5, 0)
            
            # Face arrière
            face = block_node.attachNewNode(cm.generate())
            face.setPos(0, -0.5, 0)
            face.setHpr(180, 0, 0)
            
            # Face gauche
            face = block_node.attachNewNode(cm.generate())
            face.setPos(-0.5, 0, 0)
            face.setHpr(90, 0, 0)
            
            # Face droite
            face = block_node.attachNewNode(cm.generate())
            face.setPos(0.5, 0, 0)
            face.setHpr(-90, 0, 0)
            
            # Face haut
            face = block_node.attachNewNode(cm.generate())
            face.setPos(0, 0, 0.5)
            face.setHpr(0, -90, 0)
            
            # Face bas
            face = block_node.attachNewNode(cm.generate())
            face.setPos(0, 0, -0.5)
            face.setHpr(0, 90, 0)
            
            # Positionner et colorer le bloc
            block_node.setPos(x, y, z)
            color_value = self.block_types.get(block_type, (1, 1, 1, 1))
            block_node.setColor(*color_value)
            
            self.world_blocks[(x, y, z)] = block_node
            
        except Exception as e:
            logger.error(f"Erreur création bloc en ({x}, {y}, {z}): {e}")
        
    def handle_world_update(self, message):
        """Gère les mises à jour du monde"""
        action = message.get("action")
        x, y, z = message.get("x"), message.get("y"), message.get("z")
        
        if action == "place":
            block_type = message.get("block_type")
            if (x, y, z) not in self.world_blocks:
                self.create_block(x, y, z, block_type)
                
        elif action == "remove":
            if (x, y, z) in self.world_blocks:
                self.world_blocks[(x, y, z)].removeNode()
                del self.world_blocks[(x, y, z)]
                
    def update_players(self, players_data):
        """Met à jour les positions des autres joueurs"""
        current_player_ids = set()
        
        for player_data in players_data:
            player_id = player_data["id"]
            current_player_ids.add(player_id)
            
            # Ignorer notre propre joueur
            if player_id == self.player_id:
                continue
                
            x, y, z = player_data["x"], player_data["y"], player_data["z"]
            name = player_data["name"]
            
            if player_id not in self.other_players:
                # Créer un nouveau joueur
                from panda3d.core import CardMaker
                cm = CardMaker("player")
                cm.setFrame(-0.4, 0.4, -0.4, 0.4)
                
                player_node = self.render.attachNewNode("player")
                
                # Créer un cube simple pour représenter le joueur
                for i in range(6):  # 6 faces
                    face = player_node.attachNewNode(cm.generate())
                    if i == 0:  # Face avant
                        face.setPos(0, 0.4, 0)
                    elif i == 1:  # Face arrière
                        face.setPos(0, -0.4, 0)
                        face.setHpr(180, 0, 0)
                    elif i == 2:  # Face gauche
                        face.setPos(-0.4, 0, 0)
                        face.setHpr(90, 0, 0)
                    elif i == 3:  # Face droite
                        face.setPos(0.4, 0, 0)
                        face.setHpr(-90, 0, 0)
                    elif i == 4:  # Face haut
                        face.setPos(0, 0, 0.4)
                        face.setHpr(0, -90, 0)
                    else:  # Face bas
                        face.setPos(0, 0, -0.4)
                        face.setHpr(0, 90, 0)
                
                player_node.setPos(x, y, z)
                player_node.setColor(1, 0, 0, 1)  # Rouge pour les autres joueurs
                
                # Nom du joueur au-dessus
                name_tag = OnscreenText(
                    text=name,
                    pos=(0, 0),
                    scale=0.1,
                    fg=(1, 1, 1, 1),
                    align=TextNode.ACenter
                )
                name_tag.reparentTo(player_node)
                name_tag.setPos(0, 0, 1.5)
                name_tag.setBillboardAxis()
                
                player_node.name_tag = name_tag
                self.other_players[player_id] = player_node
                
            else:
                # Mettre à jour la position
                self.other_players[player_id].setPos(x, y, z)
                
        # Supprimer les joueurs déconnectés
        for player_id in list(self.other_players.keys()):
            if player_id not in current_player_ids:
                player_node = self.other_players[player_id]
                if hasattr(player_node, 'name_tag'):
                    player_node.name_tag.removeNode()
                player_node.removeNode()
                del self.other_players[player_id]
                
    def send_position_update(self):
        """Envoie la position du joueur au serveur"""
        if self.connected and self.player_id:
            pos = self.camera.getPos()
            current_pos = (
                round(pos.x, 2),
                round(pos.y, 2), 
                round(pos.z, 2)
            )
            
            # N'envoyer que si la position a changé
            if current_pos != self.last_position:
                message = {
                    "type": "move",
                    "player_id": self.player_id,
                    "x": current_pos[0],
                    "y": current_pos[1],
                    "z": current_pos[2]
                }
                self.send_queue.put(message)
                self.last_position = current_pos
                
    def handle_block_interaction(self, action):
        """Gère l'interaction avec les blocs (placer/détruire)"""
        if not self.connected:
            return
            
        # Raycast pour trouver le bloc visé
        from panda3d.core import CollisionTraverser, CollisionNode, CollisionRay, CollisionHandlerQueue
        
        # Créer un ray depuis la caméra
        picker_node = CollisionNode('mouseRay')
        picker_np = self.camera.attachNewNode(picker_node)
        picker_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        picker_ray = CollisionRay()
        picker_ray.setOrigin(0, 0, 0)
        picker_ray.setDirection(0, 1, 0)  # Direction vers l'avant
        picker_node.addSolid(picker_ray)
        
        traverser = CollisionTraverser('traverser')
        queue = CollisionHandlerQueue()
        traverser.addCollider(picker_np, queue)
        traverser.traverse(self.render)
        
        # Nettoyer
        picker_np.removeNode()
        
        if queue.getNumEntries() > 0:
            # Prendre le premier objet touché
            queue.sortEntries()
            entry = queue.getEntry(0)
            hit_pos = entry.getSurfacePoint(self.render)
            
            if action == "place":
                # Placer sur la face touchée
                normal = entry.getSurfaceNormal(self.render)
                block_pos = hit_pos + normal * 0.5
            else:
                # Détruire le bloc touché
                block_pos = hit_pos - entry.getSurfaceNormal(self.render) * 0.5
                
            # Arrondir aux coordonnées entières
            bx = int(block_pos.x + 0.5) if block_pos.x >= 0 else int(block_pos.x - 0.5)
            by = int(block_pos.y + 0.5) if block_pos.y >= 0 else int(block_pos.y - 0.5)
            bz = int(block_pos.z + 0.5) if block_pos.z >= 0 else int(block_pos.z - 0.5)
            
            # Envoyer au serveur
            if action == "place":
                message = {
                    "type": "place_block",
                    "x": bx,
                    "y": by,
                    "z": bz,
                    "block_type": self.current_block_type
                }
            else:
                message = {
                    "type": "remove_block", 
                    "x": bx,
                    "y": by,
                    "z": bz
                }
                
            self.send_queue.put(message)
            
    def change_block_type(self, block_index):
        """Change le type de bloc sélectionné"""
        block_list = list(self.block_types.keys())
        if 0 <= block_index < len(block_list):
            self.current_block_type = block_list[block_index]
            self.block_indicator.setText(f"Bloc: {self.current_block_type.title()}")
            self.block_indicator.setFg(self.block_types[self.current_block_type])
            
    def toggle_chat(self):
        """Active/désactive le chat"""
        self.chat_visible = not self.chat_visible
        if self.chat_visible:
            self.chat_frame.show()
        else:
            self.chat_frame.hide()
            
    def add_chat_message(self, player_name, message):
        """Ajoute un message au chat"""
        timestamp = time.strftime("%H:%M")
        chat_msg = f"[{timestamp}] {player_name}: {message}"
        
        self.chat_messages.append(chat_msg)
        if len(self.chat_messages) > 10:
            self.chat_messages.pop(0)
            
        self.chat_text.setText('\n'.join(self.chat_messages))
        
    def update_game(self, task):
        """Mise à jour principale du jeu (appelée chaque frame)"""
        # Traiter les messages du serveur
        self.process_server_messages()
        
        # Envoyer position si connecté
        self.position_update_timer += globalClock.getDt()
        if self.position_update_timer > 0.1:  # 10 FPS pour les positions
            self.send_position_update()
            self.position_update_timer = 0
            
        return task.cont

def run_network_thread(client):
    """Thread pour la communication réseau"""
    async def network_main():
        # Connexion au serveur
        if await client.connect_to_server():
            # Lancer les tâches réseau
            await asyncio.gather(
                client.handle_server_messages(),
                client.send_messages_to_server()
            )
        
    asyncio.run(network_main())

def main():
    """Point d'entrée principal"""
    print("🎮 Client Minecraft-like (Panda3D)")
    print("=" * 30)
    
    try:
        # Demander les informations de connexion
        server_host = input("Adresse serveur (localhost): ").strip() or "localhost"
        try:
            server_port = int(input("Port serveur (8765): ").strip() or "8765")
        except ValueError:
            server_port = 8765
            
        player_name = input("Nom du joueur (Joueur): ").strip() or "Joueur"
        
        print(f"\n🔗 Connexion à {server_host}:{server_port} en tant que '{player_name}'...")
        
        # Créer le client
        client = MinecraftClient(server_host, server_port)
        client.player_name = player_name
        
        # Démarrer le thread réseau
        network_thread = threading.Thread(target=run_network_thread, args=(client,))
        network_thread.daemon = True
        network_thread.start()
        
        print("🎮 Démarrage de l'interface 3D...")
        print("✅ Client démarré avec succès!")
        print("🎮 Utilisez ZQSD pour vous déplacer, Espace pour sauter, clic gauche pour détruire, clic droit pour placer des blocs")
        
        # Démarrer la boucle principale de Panda3D
        client.run()
        
    except KeyboardInterrupt:
        print("\n⏹️  Client fermé par l'utilisateur")
    except ImportError as e:
        print(f"\n❌ Erreur d'importation: {e}")
        print("🔧 Assurez-vous que toutes les dépendances sont installées:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        print("🔧 Vérifiez que le serveur est démarré et accessible")

if __name__ == "__main__":
    main()