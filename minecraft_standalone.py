#!/usr/bin/env python3
"""
Minecraft Standalone - Version autonome simplifiée
==================================================

Une version autonome de Minecraft qui fonctionne sans serveur.
Ce module peut fonctionner en mode texte pour les tests ou avec interface graphique.

Usage:
    python3 minecraft_standalone.py [--text-mode] [--world WORLD_FILE]

Auteur: Assistant IA pour hackolite/cv_minecraft
"""

import sys
import math
import random
import time
import json
import argparse
import os
import pickle
from typing import Tuple, Dict, Optional, List
from collections import defaultdict

# Local imports
from client_config import config
from protocol import BlockType
from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT, GRAVITY, TERMINAL_VELOCITY, JUMP_VELOCITY
)
from noise_gen import NoiseGen

class StandaloneWorld:
    """Gestionnaire de monde autonome."""
    
    def __init__(self, size: int = 128):
        self.size = size
        self.blocks = {}  # position -> block_type
        self.spawn_position = [0, 100, 0]
        self.noise_gen = NoiseGen(random.randint(1, 1000000))
        
    def generate_terrain(self):
        """Génère le terrain initial."""
        print(f"🌍 Génération du terrain ({self.size}x{self.size})...")
        
        generated_count = 0
        for x in range(-self.size // 2, self.size // 2):
            for z in range(-self.size // 2, self.size // 2):
                # Génère la hauteur avec bruit
                height = int(self.noise_gen.getHeight(x, z))
                
                # Bedrock
                for y in range(0, 5):
                    self.blocks[(x, y, z)] = BlockType.STONE
                    generated_count += 1
                
                # Couches de pierre
                for y in range(5, height - 5):
                    self.blocks[(x, y, z)] = BlockType.STONE
                    generated_count += 1
                
                # Couche de terre
                for y in range(height - 5, height - 1):
                    self.blocks[(x, y, z)] = BlockType.SAND
                    generated_count += 1
                
                # Herbe sur le dessus
                self.blocks[(x, height - 1, z)] = BlockType.GRASS
                generated_count += 1
                
                # Arbres occasionnels
                if random.random() < 0.02 and height > 45:
                    tree_height = random.randint(3, 6)
                    # Tronc
                    for y in range(height, height + tree_height):
                        self.blocks[(x, y, z)] = BlockType.WOOD
                        generated_count += 1
                    # Feuilles
                    for dx in range(-2, 3):
                        for dz in range(-2, 3):
                            for dy in range(tree_height - 1, tree_height + 2):
                                if random.random() < 0.7:
                                    self.blocks[(x + dx, height + dy, z + dz)] = BlockType.LEAF
                                    generated_count += 1
        
        # Position de spawn sûre
        self.spawn_position = [0, self.get_ground_height(0, 0) + 3, 0]
        print(f"✅ Terrain généré: {generated_count:,} blocs")
        print(f"📍 Position de spawn: {self.spawn_position}")
    
    def get_ground_height(self, x: int, z: int) -> int:
        """Trouve la hauteur du sol à une position."""
        for y in range(120, 0, -1):
            if (x, y, z) in self.blocks:
                return y + 1
        return 50
    
    def add_block(self, position: Tuple[int, int, int], block_type: str):
        """Ajoute un bloc."""
        self.blocks[position] = block_type
        print(f"+ Bloc {block_type} ajouté à {position}")
    
    def remove_block(self, position: Tuple[int, int, int]) -> bool:
        """Retire un bloc."""
        if position in self.blocks:
            block_type = self.blocks[position]
            del self.blocks[position]
            print(f"- Bloc {block_type} retiré de {position}")
            return True
        return False
    
    def get_block(self, position: Tuple[int, int, int]) -> Optional[str]:
        """Obtient le type de bloc à une position."""
        return self.blocks.get(position)
    
    def save(self, filename: str):
        """Sauvegarde le monde."""
        try:
            data = {
                'blocks': self.blocks,
                'spawn_position': self.spawn_position,
                'size': self.size
            }
            with open(filename, 'wb') as f:
                pickle.dump(data, f)
            print(f"💾 Monde sauvegardé: {filename}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    
    def load(self, filename: str) -> bool:
        """Charge un monde."""
        try:
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                    self.blocks = data['blocks']
                    self.spawn_position = data['spawn_position']
                    self.size = data.get('size', 128)
                print(f"📁 Monde chargé: {filename}")
                return True
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
        return False

class StandalonePlayer:
    """Joueur autonome avec physique locale."""
    
    def __init__(self, world: StandaloneWorld, spawn_position: List[float] = None):
        self.world = world
        self.position = spawn_position or world.spawn_position.copy()
        self.rotation = [0.0, 0.0]  # horizontal, vertical
        self.velocity = [0.0, 0.0, 0.0]  # dx, dy, dz
        self.on_ground = False
        self.flying = False
        
        # Vitesses
        self.movement_speed = 5.0
        self.jump_speed = 8.0
        self.flying_speed = 15.0
        
        # Physique
        self.collision_detector = MinecraftCollisionDetector(world.blocks)
        self.physics = MinecraftPhysics(self.collision_detector)
        
        # État de mouvement
        self.movement_keys = {'w': False, 'a': False, 's': False, 'd': False}
        self.jumping = False
        
        print(f"🧑 Joueur créé à {self.position}")
    
    def update_physics(self, dt: float):
        """Met à jour la physique du joueur."""
        dt = min(dt, 0.2)  # Limite les gros sauts temporels
        
        # Calcule le mouvement basé sur les touches
        dx, dy, dz = self.get_movement_vector()
        
        # Applique les vitesses
        if self.flying:
            speed = self.flying_speed
            # En vol, contrôle direct de dy
            self.velocity[1] = dy * speed
        else:
            speed = self.movement_speed
            
            # Saut
            if self.jumping and self.on_ground:
                self.velocity[1] = self.jump_speed
                self.on_ground = False
                self.jumping = False
            
            # Gravité
            self.velocity[1] -= GRAVITY * dt
            self.velocity[1] = max(self.velocity[1], -TERMINAL_VELOCITY)
        
        # Mouvement horizontal
        self.velocity[0] = dx * speed
        self.velocity[2] = dz * speed
        
        # Met à jour la détection de collision
        self.collision_detector.world_blocks = self.world.blocks
        
        # Applique la physique
        old_position = tuple(self.position)
        new_position, new_velocity, new_on_ground = self.physics.update_position(
            old_position, self.velocity, dt, self.on_ground, False
        )
        
        self.position = list(new_position)
        if not self.flying:
            self.velocity = list(new_velocity)
            self.on_ground = new_on_ground
    
    def get_movement_vector(self) -> Tuple[float, float, float]:
        """Calcule le vecteur de mouvement basé sur les touches et la rotation."""
        # Mouvement relatif aux touches
        forward = -1 if self.movement_keys['w'] else (1 if self.movement_keys['s'] else 0)
        strafe = -1 if self.movement_keys['a'] else (1 if self.movement_keys['d'] else 0)
        
        if forward == 0 and strafe == 0:
            return (0.0, 0.0, 0.0)
        
        # Calcule l'angle de mouvement
        angle = math.atan2(strafe, forward)
        total_angle = math.radians(self.rotation[0]) + angle
        
        # Mouvement horizontal
        dx = math.cos(total_angle)
        dz = math.sin(total_angle)
        
        # Mouvement vertical (seulement en vol)
        dy = 0.0
        if self.flying:
            if self.movement_keys['w'] and not self.movement_keys['s']:
                dy = math.sin(math.radians(self.rotation[1]))
            elif self.movement_keys['s'] and not self.movement_keys['w']:
                dy = -math.sin(math.radians(self.rotation[1]))
        
        return (dx, dy, dz)
    
    def set_movement(self, key: str, pressed: bool):
        """Définit l'état d'une touche de mouvement."""
        if key in self.movement_keys:
            self.movement_keys[key] = pressed
    
    def jump(self):
        """Fait sauter le joueur."""
        if not self.flying:
            self.jumping = True
    
    def toggle_flying(self):
        """Active/désactive le vol."""
        self.flying = not self.flying
        print(f"✈️ Vol {'activé' if self.flying else 'désactivé'}")
    
    def look(self, dx: float, dy: float):
        """Change la direction du regard."""
        self.rotation[0] += dx
        self.rotation[1] = max(-90, min(90, self.rotation[1] + dy))
    
    def get_look_vector(self) -> Tuple[float, float, float]:
        """Obtient le vecteur de visée."""
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)
    
    def hit_test(self, max_distance: int = 8) -> Tuple[Optional[Tuple[int, int, int]], 
                                                       Optional[Tuple[int, int, int]]]:
        """Test de collision pour la visée."""
        m = 8  # Précision
        x, y, z = self.position
        dx, dy, dz = self.get_look_vector()
        previous = None
        
        for _ in range(max_distance * m):
            # Position actuelle du rayon
            current = (int(round(x)), int(round(y)), int(round(z)))
            
            if current != previous and current in self.world.blocks:
                return current, previous  # bloc touché, position pour placer
            
            previous = current
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        
        return None, None

class TextModeInterface:
    """Interface en mode texte pour tester le jeu."""
    
    def __init__(self, world: StandaloneWorld, player: StandalonePlayer):
        self.world = world
        self.player = player
        self.running = True
        self.commands = {
            'quit': self.cmd_quit,
            'q': self.cmd_quit,
            'help': self.cmd_help,
            'h': self.cmd_help,
            'status': self.cmd_status,
            'move': self.cmd_move,
            'look': self.cmd_look,
            'fly': self.cmd_fly,
            'jump': self.cmd_jump,
            'place': self.cmd_place,
            'break': self.cmd_break,
            'save': self.cmd_save,
            'load': self.cmd_load,
            'tp': self.cmd_teleport,
        }
    
    def run(self):
        """Lance l'interface en mode texte."""
        print("\n🎮 Minecraft Standalone - Mode Texte")
        print("Tapez 'help' pour voir les commandes disponibles")
        print("=" * 50)
        
        while self.running:
            try:
                # Affiche la position actuelle
                x, y, z = [round(coord, 1) for coord in self.player.position]
                command = input(f"\n[{x}, {y}, {z}] > ").strip().lower()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                if cmd in self.commands:
                    self.commands[cmd](args)
                else:
                    print(f"❌ Commande inconnue: {cmd}")
                    print("Tapez 'help' pour voir les commandes disponibles")
                
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir!")
                break
            except EOFError:
                break
    
    def cmd_help(self, args):
        """Affiche l'aide."""
        print("\n📚 Commandes disponibles:")
        print("  help, h           - Affiche cette aide")
        print("  quit, q           - Quitte le jeu")
        print("  status            - Affiche l'état du joueur")
        print("  move <x> <y> <z>  - Bouge le joueur")
        print("  look <h> <v>      - Change la direction du regard")
        print("  fly               - Active/désactive le vol")
        print("  jump              - Fait sauter le joueur")
        print("  place <type>      - Place un bloc devant soi")
        print("  break             - Détruit le bloc visé")
        print("  save <file>       - Sauvegarde le monde")
        print("  load <file>       - Charge un monde")
        print("  tp <x> <y> <z>    - Téléporte le joueur")
        print("\nTypes de blocs: grass, stone, wood, sand, brick")
    
    def cmd_quit(self, args):
        """Quitte le jeu."""
        self.running = False
        print("👋 Au revoir!")
    
    def cmd_status(self, args):
        """Affiche l'état du joueur."""
        x, y, z = self.player.position
        h, v = self.player.rotation
        vx, vy, vz = self.player.velocity
        
        print(f"\n📍 Position: {x:.1f}, {y:.1f}, {z:.1f}")
        print(f"👁️  Rotation: {h:.1f}°, {v:.1f}°")
        print(f"💨 Vitesse: {vx:.1f}, {vy:.1f}, {vz:.1f}")
        print(f"🌍 Sol: {'Oui' if self.player.on_ground else 'Non'}")
        print(f"✈️  Vol: {'Oui' if self.player.flying else 'Non'}")
        print(f"📦 Blocs dans le monde: {len(self.world.blocks):,}")
    
    def cmd_move(self, args):
        """Bouge le joueur."""
        if len(args) != 3:
            print("❌ Usage: move <x> <y> <z>")
            return
        
        try:
            dx, dy, dz = map(float, args)
            self.player.position[0] += dx
            self.player.position[1] += dy
            self.player.position[2] += dz
            print(f"🚶 Bougé de {dx}, {dy}, {dz}")
        except ValueError:
            print("❌ Coordonnées invalides")
    
    def cmd_look(self, args):
        """Change la direction du regard."""
        if len(args) != 2:
            print("❌ Usage: look <horizontal> <vertical>")
            return
        
        try:
            dh, dv = map(float, args)
            self.player.look(dh, dv)
            print(f"👁️  Rotation changée de {dh}°, {dv}°")
        except ValueError:
            print("❌ Angles invalides")
    
    def cmd_fly(self, args):
        """Active/désactive le vol."""
        self.player.toggle_flying()
    
    def cmd_jump(self, args):
        """Fait sauter le joueur."""
        if self.player.flying:
            print("⚠️  Impossible de sauter en vol")
        else:
            self.player.jump()
            print("🦘 Saut!")
    
    def cmd_place(self, args):
        """Place un bloc."""
        if len(args) != 1:
            print("❌ Usage: place <type>")
            print("Types: grass, stone, wood, sand, brick")
            return
        
        block_type = args[0].lower()
        valid_types = ['grass', 'stone', 'wood', 'sand', 'brick']
        
        if block_type not in valid_types:
            print(f"❌ Type de bloc invalide: {block_type}")
            print(f"Types valides: {', '.join(valid_types)}")
            return
        
        # Trouve la position pour placer le bloc
        hit_block, place_pos = self.player.hit_test()
        
        if place_pos:
            self.world.add_block(place_pos, block_type)
        else:
            print("❌ Aucune surface trouvée pour placer le bloc")
    
    def cmd_break(self, args):
        """Détruit le bloc visé."""
        hit_block, _ = self.player.hit_test()
        
        if hit_block:
            if self.world.remove_block(hit_block):
                print("🔨 Bloc détruit!")
            else:
                print("❌ Aucun bloc à cette position")
        else:
            print("❌ Aucun bloc visé")
    
    def cmd_save(self, args):
        """Sauvegarde le monde."""
        filename = args[0] if args else "world_standalone.dat"
        self.world.save(filename)
    
    def cmd_load(self, args):
        """Charge un monde."""
        filename = args[0] if args else "world_standalone.dat"
        if self.world.load(filename):
            # Met à jour la détection de collision
            self.player.collision_detector.world_blocks = self.world.blocks
            print("🔄 Détection de collision mise à jour")
    
    def cmd_teleport(self, args):
        """Téléporte le joueur."""
        if len(args) != 3:
            print("❌ Usage: tp <x> <y> <z>")
            return
        
        try:
            x, y, z = map(float, args)
            self.player.position = [x, y, z]
            print(f"🚀 Téléporté à {x}, {y}, {z}")
        except ValueError:
            print("❌ Coordonnées invalides")

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Minecraft Standalone")
    parser.add_argument('--text-mode', action='store_true', 
                       help='Lance en mode texte (pour tests)')
    parser.add_argument('--world', '-w', help='Fichier de monde à charger')
    parser.add_argument('--size', '-s', type=int, default=64, 
                       help='Taille du monde (défaut: 64)')
    parser.add_argument('--no-generate', action='store_true',
                       help='Ne génère pas de terrain (monde vide)')
    
    args = parser.parse_args()
    
    print("🎮 Minecraft Standalone")
    print("=" * 30)
    
    # Crée le monde
    world = StandaloneWorld(args.size)
    
    # Charge un monde existant ou génère un nouveau
    if args.world and world.load(args.world):
        print(f"📁 Monde chargé: {args.world}")
    elif not args.no_generate:
        world.generate_terrain()
    else:
        print("🌍 Monde vide créé")
    
    # Crée le joueur
    player = StandalonePlayer(world)
    
    if args.text_mode:
        # Mode texte pour les tests
        interface = TextModeInterface(world, player)
        interface.run()
    else:
        # Essaie de lancer l'interface graphique
        try:
            print("🖥️  Tentative de lancement de l'interface graphique...")
            from minecraft_client_standalone import StandaloneMinecraftWindow, setup_opengl
            import pyglet
            
            setup_opengl()
            window = StandaloneMinecraftWindow(
                width=1280, height=720,
                caption='Minecraft Standalone',
                resizable=True
            )
            
            # Utilise le monde et joueur créés
            window.model.world = world.blocks
            window.position = tuple(player.position)
            
            print("✅ Interface graphique lancée!")
            pyglet.app.run()
            
        except ImportError as e:
            print(f"⚠️  Interface graphique non disponible: {e}")
            print("🔄 Basculement en mode texte...")
            interface = TextModeInterface(world, player)
            interface.run()
        except Exception as e:
            print(f"❌ Erreur interface graphique: {e}")
            print("🔄 Basculement en mode texte...")
            interface = TextModeInterface(world, player)
            interface.run()

if __name__ == '__main__':
    main()