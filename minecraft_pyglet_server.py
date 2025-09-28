#!/usr/bin/env python3
"""
Minecraft Pyglet Image Server
============================

Serveur d'images basé sur pyglet pour fournir une vue alternative du monde Minecraft.
Inspiré du code mini_minecraft_pyglet_server_corrected.py fourni dans la demande.

Ce serveur:
- Utilise le rendu pyglet du client Minecraft existant
- Capture périodiquement des images du monde 
- Les sert via FastAPI sur l'endpoint /view
- Fonctionne en parallèle avec le client principal

Usage:
    python3 minecraft_pyglet_server.py [--port 8080] [--capture-interval 0.1]
"""

import threading
import time
import io
import argparse
import sys
import os
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

# Configuration de l'environnement d'affichage avant l'import pyglet
def setup_display_environment():
    """Configure display environment for headless operation if needed."""
    if not os.environ.get('DISPLAY'):
        print("⚠️  Aucun affichage détecté. Configuration pour mode headless...")
        os.environ['DISPLAY'] = ':99'  # Défaut Xvfb
        
        # Essayer de démarrer Xvfb si disponible
        try:
            import subprocess
            import shutil
            if shutil.which('Xvfb'):
                # Vérifier si Xvfb tourne déjà sur :99
                try:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    if 'Xvfb :99' in result.stdout:
                        print("💡 Xvfb déjà actif sur :99")
                    else:
                        print("🖥️  Démarrage de Xvfb...")
                        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'], 
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(2)  # Attendre que Xvfb démarre
                        print("✅ Xvfb démarré sur :99")
                except Exception as e:
                    print(f"⚠️  Impossible de démarrer Xvfb: {e}")
            else:
                print("💡 Xvfb non disponible. Installez avec: sudo apt-get install xvfb")
        except ImportError:
            print("💡 Subprocess non disponible pour Xvfb")

# Configurer l'environnement avant d'importer Pyglet
setup_display_environment()

# Import pyglet avec gestion d'erreurs
try:
    import pyglet
    from pyglet.gl import *
    PYGLET_AVAILABLE = True
    print("✅ Pyglet importé avec succès")
except ImportError as e:
    PYGLET_AVAILABLE = False
    print(f"⚠️  Erreur lors de l'import Pyglet: {e}")
    print("🔧 Fonctionnement en mode dégradé sans rendu graphique")
    
    # Classes dummy pour la compatibilité
    class DummyWindow:
        def __init__(self, width, height, title, visible=True):
            self.width = width
            self.height = height
            self.visible = visible
        def clear(self): pass
        def get_size(self): return (self.width, self.height)
        def switch_to(self): pass
        def set_visible(self, visible): self.visible = visible
        def close(self): pass
        def dispatch_event(self, event, *args): pass
    
    class DummyClock:
        @staticmethod
        def schedule_interval(func, interval): pass
    
    class DummyApp:
        @staticmethod
        def run(): 
            print("Mode dégradé: simulation de la boucle pyglet")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    
    class pyglet:
        window = type('', (), {'Window': DummyWindow})()
        clock = DummyClock()
        app = DummyApp()
    
    # Constantes OpenGL dummy
    GL_DEPTH_TEST = 0
    GL_PROJECTION = 0
    GL_MODELVIEW = 0
    GL_QUADS = 0
    GL_RGB = 0
    GL_UNSIGNED_BYTE = 0
    GLubyte = int
    
    def glEnable(x): pass
    def glDisable(x): pass
    def glMatrixMode(x): pass
    def glLoadIdentity(): pass
    def glFrustum(*args): pass
    def glOrtho(*args): pass
    def glTranslatef(*args): pass
    def glRotatef(*args): pass
    def glBegin(x): pass
    def glEnd(): pass
    def glColor3f(*args): pass
    def glVertex3f(*args): pass
    def glReadPixels(*args): pass

# Import des composants Minecraft existants
try:
    from minecraft_client_fr import (
        MinecraftWindow, EnhancedClientModel, AdvancedNetworkClient,
        BlockType, setup_opengl
    )
    from client_config import config
    MINECRAFT_AVAILABLE = True
    print("✅ Composants Minecraft importés avec succès")
except ImportError as e:
    MINECRAFT_AVAILABLE = False
    print(f"⚠️  Composants Minecraft non disponibles: {e}")
    print("🔧 Fonctionnement en mode dégradé")
    
    # Classes dummy pour la compatibilité
    class BlockType:
        GRASS = "grass"
        STONE = "stone"
    
    def setup_opengl(): pass

# --- CONFIGURATION SERVEUR ---
DEFAULT_PORT = 8080
DEFAULT_CAPTURE_INTERVAL = 0.1
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600

# Variables globales pour le partage d'images entre threads
latest_image = None
image_lock = threading.Lock()
server_running = False

# --- FASTAPI APPLICATION ---
app = FastAPI(title="Minecraft Pyglet Image Server", version="1.0.0")

@app.get("/")
async def home():
    """Page d'accueil de l'API."""
    return {
        "message": "Minecraft Pyglet Image Server",
        "status": "running" if server_running else "stopped",
        "endpoints": {
            "view": "/view",
            "status": "/status"
        },
        "minecraft_available": MINECRAFT_AVAILABLE
    }

@app.get("/view")
async def get_view():
    """Récupère la vue actuelle du monde Minecraft."""
    with image_lock:
        if latest_image is None:
            # Retourner une image vide si pas encore disponible
            img = Image.new('RGB', (WINDOW_WIDTH, WINDOW_HEIGHT), (0, 0, 0))
        else:
            img = latest_image.copy()
    
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return StreamingResponse(bio, media_type="image/png")

@app.get("/status")
async def get_status():
    """Récupère le statut du serveur."""
    return {
        "server_running": server_running,
        "minecraft_available": MINECRAFT_AVAILABLE,
        "has_latest_image": latest_image is not None,
        "window_size": f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
    }

def run_fastapi_server(host: str = "127.0.0.1", port: int = DEFAULT_PORT):
    """Lance le serveur FastAPI dans un thread séparé."""
    global server_running
    server_running = True
    print(f"🚀 Démarrage du serveur FastAPI sur http://{host}:{port}")
    print(f"📸 Accédez aux images via: http://{host}:{port}/view")
    uvicorn.run(app, host=host, port=port, log_level="warning")

# --- CLASSE FENETRE MINECRAFT SIMPLIFIEE ---
class MinecraftImageWindow:
    """Fenêtre Minecraft simplifiée pour la capture d'images."""
    
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        self.width = width
        self.height = height
        self.window = None
        self.model = None
        self.setup_window()
        
    def setup_window(self):
        """Configure la fenêtre pyglet."""
        try:
            if not PYGLET_AVAILABLE:
                # Mode dégradé: créer une fenêtre dummy
                self.window = pyglet.window.Window(self.width, self.height, "Minecraft Image Server", visible=False)
                print("✅ Fenêtre dummy configurée (mode dégradé)")
                return
            
            # Créer la fenêtre pyglet
            self.window = pyglet.window.Window(
                self.width, 
                self.height, 
                "Minecraft Image Server",
                visible=False  # Fenêtre invisible pour le serveur
            )
            
            # Configuration OpenGL de base
            setup_opengl()
            
            # Initialiser le modèle si disponible
            if MINECRAFT_AVAILABLE:
                self.model = EnhancedClientModel()
                self.setup_minecraft_world()
            
            # Configurer les événements
            self.setup_events()
            
            print("✅ Fenêtre pyglet configurée")
            
        except Exception as e:
            print(f"⚠️  Erreur configuration fenêtre: {e}")
            # Fallback vers une fenêtre dummy
            self.window = pyglet.window.Window(self.width, self.height, "Minecraft Image Server", visible=False)
            print("✅ Fenêtre dummy configurée (fallback)")
    
    def setup_minecraft_world(self):
        """Configure un monde Minecraft basique pour les tests."""
        if not self.model:
            return
            
        try:
            # Ajouter quelques blocs de test
            for x in range(-5, 6):
                for z in range(-5, 6):
                    # Sol en herbe
                    self.model.add_block((x, 0, z), BlockType.GRASS)
                    # Quelques blocs aléatoires
                    if abs(x) + abs(z) < 3:
                        self.model.add_block((x, 1, z), BlockType.STONE)
            
            print("✅ Monde Minecraft de test créé")
            
        except Exception as e:
            print(f"⚠️  Erreur création monde: {e}")
    
    def setup_events(self):
        """Configure les événements pyglet."""
        if not self.window:
            return
            
        @self.window.event
        def on_draw():
            self.draw()
    
    def draw(self):
        """Rendu principal de la scène."""
        if not self.window:
            return
        
        if not PYGLET_AVAILABLE:
            # Mode dégradé: pas de rendu réel
            return
            
        self.window.clear()
        
        # Configuration 3D
        self.set_3d()
        
        # Rendu du monde Minecraft si disponible
        if self.model and MINECRAFT_AVAILABLE:
            try:
                glColor3d(1, 1, 1)
                self.model.batch.draw()
            except Exception as e:
                print(f"⚠️  Erreur rendu Minecraft: {e}")
        else:
            # Rendu de test simple
            self.draw_test_scene()
        
        # Retour au mode 2D pour l'interface
        self.set_2d()
    
    def set_3d(self):
        """Configure OpenGL pour le rendu 3D."""
        if not PYGLET_AVAILABLE:
            return
            
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # Perspective
        glFrustum(-1, 1, -1, 1, 1, 100)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Position de la caméra
        glTranslatef(0, -5, -10)
        glRotatef(45, 1, 0, 0)
    
    def set_2d(self):
        """Configure OpenGL pour le rendu 2D."""
        if not PYGLET_AVAILABLE:
            return
            
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def draw_test_scene(self):
        """Dessine une scène de test simple."""
        if not PYGLET_AVAILABLE:
            return
            
        try:
            # Dessiner un cube coloré simple
            glBegin(GL_QUADS)
            
            # Face avant (rouge)
            glColor3f(1.0, 0.0, 0.0)
            glVertex3f(-1, -1, 1)
            glVertex3f(1, -1, 1)
            glVertex3f(1, 1, 1)
            glVertex3f(-1, 1, 1)
            
            # Face arrière (vert)
            glColor3f(0.0, 1.0, 0.0)
            glVertex3f(-1, -1, -1)
            glVertex3f(-1, 1, -1)
            glVertex3f(1, 1, -1)
            glVertex3f(1, -1, -1)
            
            # Face du haut (bleu)
            glColor3f(0.0, 0.0, 1.0)
            glVertex3f(-1, 1, -1)
            glVertex3f(-1, 1, 1)
            glVertex3f(1, 1, 1)
            glVertex3f(1, 1, -1)
            
            # Face du bas (jaune)
            glColor3f(1.0, 1.0, 0.0)
            glVertex3f(-1, -1, -1)
            glVertex3f(1, -1, -1)
            glVertex3f(1, -1, 1)
            glVertex3f(-1, -1, 1)
            
            # Face droite (magenta)
            glColor3f(1.0, 0.0, 1.0)
            glVertex3f(1, -1, -1)
            glVertex3f(1, 1, -1)
            glVertex3f(1, 1, 1)
            glVertex3f(1, -1, 1)
            
            # Face gauche (cyan)
            glColor3f(0.0, 1.0, 1.0)
            glVertex3f(-1, -1, -1)
            glVertex3f(-1, -1, 1)
            glVertex3f(-1, 1, 1)
            glVertex3f(-1, 1, -1)
            
            glEnd()
            
        except Exception as e:
            print(f"⚠️  Erreur rendu scène test: {e}")

def capture_frame(dt):
    """Capture l'image du buffer dans le thread principal de Pyglet."""
    global latest_image
    
    if not minecraft_window or not minecraft_window.window:
        return
    
    if not PYGLET_AVAILABLE:
        # Mode dégradé: créer une image de test
        try:
            width, height = minecraft_window.window.get_size()
            # Créer une image de test colorée
            img = Image.new('RGB', (width, height), (50, 100, 150))
            
            # Ajouter du contenu visuel simple
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Dessiner des formes de test
            draw.rectangle([50, 50, width-50, height-50], outline=(255, 255, 255), width=3)
            draw.text((width//2-50, height//2), "Mode Dégradé", fill=(255, 255, 255))
            draw.text((width//2-80, height//2+20), f"Taille: {width}x{height}", fill=(255, 255, 255))
            
            # Stocker l'image de manière thread-safe
            with image_lock:
                latest_image = img
                
        except Exception as e:
            print(f"⚠️  Erreur capture frame (mode dégradé): {e}")
        return
        
    try:
        # S'assurer que le contexte OpenGL est correct
        minecraft_window.window.switch_to()
        
        # Forcer un rendu
        minecraft_window.draw()
        
        # Lire les pixels du framebuffer
        width, height = minecraft_window.window.get_size()
        pixels = (GLubyte * (3 * width * height))(0)
        glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, pixels)
        
        # Convertir en image PIL
        img = Image.frombytes('RGB', (width, height), pixels)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Stocker l'image de manière thread-safe
        with image_lock:
            latest_image = img
            
    except Exception as e:
        print(f"⚠️  Erreur capture frame: {e}")

# Variable globale pour la fenêtre
minecraft_window = None

def main():
    """Point d'entrée principal."""
    global minecraft_window, server_running
    
    parser = argparse.ArgumentParser(description="Minecraft Pyglet Image Server")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                       help=f'Port du serveur FastAPI (défaut: {DEFAULT_PORT})')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Adresse IP du serveur (défaut: 127.0.0.1)')
    parser.add_argument('--capture-interval', type=float, default=DEFAULT_CAPTURE_INTERVAL,
                       help=f'Intervalle de capture en secondes (défaut: {DEFAULT_CAPTURE_INTERVAL})')
    parser.add_argument('--visible', action='store_true',
                       help='Rendre la fenêtre visible (pour debug)')
    
    args = parser.parse_args()
    
    print("🎮 Démarrage du serveur d'images Minecraft Pyglet")
    print("=" * 50)
    
    # Lancer le serveur FastAPI en thread séparé
    server_thread = threading.Thread(
        target=run_fastapi_server, 
        args=(args.host, args.port),
        daemon=True
    )
    server_thread.start()
    
    # Créer la fenêtre Minecraft
    print("🖼️  Initialisation de la fenêtre Minecraft...")
    minecraft_window = MinecraftImageWindow()
    
    if minecraft_window.window:
        # Rendre visible si demandé
        if args.visible:
            minecraft_window.window.set_visible(True)
        
        # Planifier la capture d'image périodique (dans le thread principal pyglet)
        pyglet.clock.schedule_interval(capture_frame, args.capture_interval)
        
        print(f"📸 Capture d'images programmée toutes les {args.capture_interval}s")
        print(f"🌐 Serveur accessible sur http://{args.host}:{args.port}")
        print(f"🖼️  Images disponibles sur http://{args.host}:{args.port}/view")
        print()
        print("Appuyez sur Ctrl+C pour arrêter le serveur")
        
        try:
            # Démarrer la boucle principale pyglet
            pyglet.app.run()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur demandé par l'utilisateur")
        finally:
            server_running = False
            
    else:
        print("❌ Impossible de créer la fenêtre Minecraft")
        server_running = False
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())