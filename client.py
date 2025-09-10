#!/usr/bin/env python3
"""
Client Minecraft-like en Python avec Ursina
Interface 3D et communication WebSocket avec le serveur
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import asyncio
import websockets
import json
import threading
import queue
import time
from typing import Dict, List
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinecraftClient:
    def __init__(self, server_host="localhost", server_port=8765):
        self.server_host = server_host
        self.server_port = server_port
        self.websocket = None
        self.player_id = None
        self.player_name = "Joueur"
        
        # Files pour la communication entre threads
        self.message_queue = queue.Queue()
        self.send_queue = queue.Queue()
        
        # Stockage des entités du jeu
        self.world_blocks: Dict[tuple, Entity] = {}
        self.other_players: Dict[str, Entity] = {}
        
        # Types de blocs et leurs couleurs
        self.block_types = {
            "grass": color.green,
            "stone": color.gray,
            "wood": color.brown,
            "dirt": color.brown,
            "sand": color.yellow,
            "water": color.blue
        }
        
        self.current_block_type = "grass"
        
        # Variables de jeu
        self.connected = False
        self.last_position = (0, 0, 0)
        self.position_update_timer = 0
        
        # Interface
        self.chat_messages = []
        self.chat_visible = False
        self.chat_input = None
        
    def setup_ursina(self):
        """Initialise Ursina et la scène 3D"""
        app = Ursina()
        
        # Configuration de la fenêtre
        window.title = "Minecraft-like Client"
        window.borderless = False
        window.fullscreen = False
        window.exit_button.visible = False
        window.fps_counter.enabled = True
        
        # Ciel
        sky = Sky()
        
        # Contrôleur de joueur avec gravité et saut
        self.player = FirstPersonController()
        self.player.cursor.visible = False
        
        # Configuration de la gravité et du mouvement
        # Note: certaines propriétés peuvent ne pas exister selon la version d'Ursina
        try:
            self.player.gravity = 1  # Activer la gravité
        except:
            pass
        try:
            self.player.jump_height = 2  # Hauteur de saut
        except:
            self.player.jump_height = 2  # Fallback
        try:
            self.player.speed = 5  # Vitesse de déplacement
        except:
            pass
        try:
            self.player.mouse_sensitivity = 50  # Sensibilité de la souris
        except:
            pass
        
        # Caméra
        camera.fov = 90
        
        # Interface utilisateur
        self.setup_ui()
        
        # Lumière
        DirectionalLight().look_at(Vec3(1, -1, -1))
        
        return app
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Texte d'information
        self.info_text = Text(
            "🎮 Minecraft-like\n" +
            "ZQSD: Déplacer | Espace: Sauter | Clic gauche: Détruire | Clic droit: Placer\n" +
            "1-6: Changer bloc | T: Chat | ESC: Quitter",
            position=(-0.95, 0.45),
            scale=0.7,
            color=color.white
        )
        
        # Indicateur de bloc sélectionné
        self.block_indicator = Text(
            f"Bloc: {self.current_block_type.title()}",
            position=(0.7, 0.45),
            scale=0.8,
            color=self.block_types.get(self.current_block_type, color.white)
        )
        
        # Statut de connexion
        self.connection_status = Text(
            "Connexion...",
            position=(-0.95, -0.45),
            scale=0.7,
            color=color.red
        )
        
        # Zone de chat
        self.chat_panel = Entity(parent=camera.ui, model='quad', 
                               color=color.dark_gray, scale=(0.8, 0.3), 
                               position=(-0.1, -0.2), alpha=0.7, visible=False)
        
        self.chat_text = Text('', parent=self.chat_panel, position=(0, 0.1), 
                             scale=0.5, color=color.white, visible=False)
        
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
                    self.connection_status.text = f"Connecté (ID: {self.player_id[:8]})"
                    self.connection_status.color = color.green
                    
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
            destroy(block)
        self.world_blocks.clear()
        
        # Charger les nouveaux blocs
        for block_data in world_data:
            self.create_block(
                block_data["x"],
                block_data["y"], 
                block_data["z"],
                block_data["block_type"]
            )
            
    def create_block(self, x, y, z, block_type):
        """Crée un bloc visuel dans le monde"""
        color_value = self.block_types.get(block_type, color.white)
        
        block = Entity(
            model='cube',
            color=color_value,
            position=(x, y, z),
            texture='white_cube'
        )
        
        self.world_blocks[(x, y, z)] = block
        
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
                destroy(self.world_blocks[(x, y, z)])
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
                player_entity = Entity(
                    model='cube',
                    color=color.red,
                    position=(x, y, z),
                    scale=0.8
                )
                
                # Nom du joueur au-dessus
                name_tag = Text(
                    name,
                    parent=player_entity,
                    position=(0, 1.5, 0),
                    scale=2,
                    color=color.white,
                    billboard=True
                )
                
                player_entity.name_tag = name_tag
                self.other_players[player_id] = player_entity
                
            else:
                # Mettre à jour la position
                self.other_players[player_id].position = (x, y, z)
                
        # Supprimer les joueurs déconnectés
        for player_id in list(self.other_players.keys()):
            if player_id not in current_player_ids:
                player_entity = self.other_players[player_id]
                destroy(player_entity.name_tag)
                destroy(player_entity)
                del self.other_players[player_id]
                
    def send_position_update(self):
        """Envoie la position du joueur au serveur"""
        if self.connected and self.player_id:
            current_pos = (
                round(self.player.x, 2),
                round(self.player.y, 2), 
                round(self.player.z, 2)
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
        hit_info = raycast(
            origin=camera.world_position,
            direction=camera.forward,
            distance=5,
            ignore=[self.player]
        )
        
        if hit_info.hit:
            # Calculer la position du bloc
            if action == "place":
                # Placer sur la face touchée
                block_pos = hit_info.world_point + hit_info.normal * 0.5
            else:
                # Détruire le bloc touché
                block_pos = hit_info.world_point - hit_info.normal * 0.5
                
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
            self.block_indicator.text = f"Bloc: {self.current_block_type.title()}"
            self.block_indicator.color = self.block_types[self.current_block_type]
            
    def toggle_chat(self):
        """Active/désactive le chat"""
        self.chat_visible = not self.chat_visible
        self.chat_panel.visible = self.chat_visible
        self.chat_text.visible = self.chat_visible
        
        if self.chat_visible:
            mouse.locked = False
            self.player.cursor.visible = True
        else:
            mouse.locked = True  
            self.player.cursor.visible = False
            
    def add_chat_message(self, player_name, message):
        """Ajoute un message au chat"""
        timestamp = time.strftime("%H:%M")
        chat_msg = f"[{timestamp}] {player_name}: {message}"
        
        self.chat_messages.append(chat_msg)
        if len(self.chat_messages) > 10:
            self.chat_messages.pop(0)
            
        self.chat_text.text = '\n'.join(self.chat_messages)
        
    def update_game(self):
        """Mise à jour principale du jeu (appelée chaque frame)"""
        # Traiter les messages du serveur
        self.process_server_messages()
        
        # Envoyer position si connecté
        self.position_update_timer += time.dt
        if self.position_update_timer > 0.1:  # 10 FPS pour les positions
            self.send_position_update()
            self.position_update_timer = 0
            
        # Gestion des entrées
        if held_keys['escape']:
            application.quit()
            
        # Saut avec la barre d'espace
        if held_keys['space']:
            # Le FirstPersonController d'Ursina gère le saut avec gravity
            # On peut aussi utiliser player.y += jump_speed si besoin
            if hasattr(self.player, 'jump'):
                try:
                    self.player.jump()
                except:
                    # Fallback pour saut manuel si jump() n'existe pas
                    if self.player.grounded:
                        self.player.velocity_y = self.player.jump_height
            
        # Changement de bloc (touches 1-6)
        for i in range(1, 7):
            if held_keys[str(i)]:
                self.change_block_type(i - 1)
                
        # Chat
        if held_keys['t'] and not self.chat_visible:
            self.toggle_chat()
            
        # Interactions avec les blocs
        if mouse.left:
            self.handle_block_interaction("remove")
        elif mouse.right:
            self.handle_block_interaction("place")

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
    print("🎮 Client Minecraft-like")
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
        
        # Initialiser Ursina et démarrer le jeu
        app = client.setup_ursina()
        
        # Boucle principale
        def update():
            client.update_game()
        
        print("✅ Client démarré avec succès!")
        print("🎮 Utilisez ZQSD pour vous déplacer, Espace pour sauter, clic gauche pour détruire, clic droit pour placer des blocs")
        app.run()
        
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
