#!/usr/bin/env python3
"""
Observer Camera System for RTSP Streaming
System de caméra d'observateur pour streaming RTSP

Ce module implémente la capture d'images depuis la perspective des observateurs RTSP.
"""

import time
import threading
import numpy as np
from typing import Optional, Tuple, List
import io

# Try to import OpenGL/Pyglet, but make it optional
import os
HAS_OPENGL = False
HAS_FULL_GL = False

# Only try to import pyglet if we have a display or if running in container/headless with xvfb
display_available = bool(os.environ.get('DISPLAY'))

if display_available:
    try:
        import pyglet
        from pyglet.gl import *
        HAS_OPENGL = True
        
        # Ensure we have all the GL constants we need
        try:
            test_constants = [GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, 
                             GL_PROJECTION, GL_MODELVIEW, GL_QUADS, GL_RGB, GL_UNSIGNED_BYTE,
                             GL_PACK_ALIGNMENT]
            HAS_FULL_GL = True
        except NameError:
            print("Warning: Some OpenGL constants missing, using fallbacks")
            HAS_FULL_GL = False
        
        # Import additional OpenGL functions from PyOpenGL if needed for compatibility
        try:
            from OpenGL.GL import (glReadPixels as PyOpenGL_glReadPixels,
                                   glMatrixMode, glLoadIdentity, glViewport,
                                   glRotatef, glTranslatef, glMultMatrixf,
                                   glBegin, glEnd, glVertex3f, glColor3f,
                                   glPixelStorei, glClearColor, glClear, glEnable,
                                   GL_MODELVIEW, GL_PROJECTION)
            # Replace pyglet's glReadPixels with PyOpenGL's version for compatibility
            glReadPixels = PyOpenGL_glReadPixels
            print("✓ OpenGL functions imported from PyOpenGL for compatibility")
        except ImportError:
            print("Warning: PyOpenGL not available, may have compatibility issues")
            
    except Exception as e:
        print(f"Warning: Could not import OpenGL/Pyglet: {e}")
        HAS_OPENGL = False
        HAS_FULL_GL = False
else:
    print("No display available - observer cameras will use test frames")

# Import math for camera calculations
import math

try:
    from PIL import Image
except ImportError:
    Image = None
    print("Warning: PIL not installed, frame capture will be limited")


class ObserverCamera:
    """Caméra d'observateur qui capture des frames depuis une position donnée."""
    
    def __init__(self, observer_id: str, position: Tuple[float, float, float], 
                 rotation: Tuple[float, float], resolution: Tuple[int, int] = (640, 480)):
        """
        Initialise une caméra d'observateur.
        
        Args:
            observer_id: ID unique de l'observateur
            position: Position (x, y, z) dans le monde
            rotation: Rotation (yaw, pitch) en degrés
            resolution: Résolution (width, height) de la capture
        """
        self.observer_id = observer_id
        self.position = position
        self.rotation = rotation
        self.resolution = resolution
        self.is_capturing = False
        self.capture_thread = None
        self.frame_buffer = []
        self.max_buffer_size = 30  # 1 seconde à 30 FPS
        self.fps = 30
        self.last_frame_time = 0
        
        # Mutex pour l'accès concurrent au buffer
        self.buffer_lock = threading.Lock()
        
        # Contexte de rendu 3D
        self._render_context = None
        
        # Initialiser le contexte de rendu si OpenGL est disponible
        if HAS_OPENGL:
            self._create_render_context()
        
    def start_capture(self, world_model):
        """Démarre la capture de frames."""
        if self.is_capturing:
            return
            
        self.is_capturing = True
        self.world_model = world_model
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
    def stop_capture(self):
        """Arrête la capture de frames."""
        self.is_capturing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        
        # Nettoyer le contexte de rendu
        if self._render_context:
            try:
                self._render_context.close()
            except:
                pass
            self._render_context = None
            
    def _capture_loop(self):
        """Boucle principale de capture."""
        frame_duration = 1.0 / self.fps
        
        while self.is_capturing:
            start_time = time.time()
            
            try:
                frame = self._capture_frame()
                if frame is not None:
                    with self.buffer_lock:
                        # Ajouter le frame au buffer
                        self.frame_buffer.append({
                            'data': frame,
                            'timestamp': time.time(),
                            'position': self.position,
                            'rotation': self.rotation
                        })
                        
                        # Limiter la taille du buffer
                        if len(self.frame_buffer) > self.max_buffer_size:
                            self.frame_buffer.pop(0)
                            
            except Exception as e:
                print(f"Erreur capture frame observateur {self.observer_id}: {e}")
                
            # Maintenir le framerate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_duration - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    def _capture_frame(self) -> Optional[bytes]:
        """
        Capture un frame depuis la perspective de l'observateur.
        Rendu la vue 3D du monde depuis cette position/rotation.
        """
        if not HAS_OPENGL or not self.world_model:
            # Fallback vers les frames de test si pas d'OpenGL ou de monde
            return self._generate_test_frame()
        
        try:
            return self._render_3d_world_frame()
        except Exception as e:
            print(f"Erreur rendu 3D observateur {self.observer_id}: {e}")
            # Fallback vers frame de test en cas d'erreur
            return self._generate_test_frame()
        
    def _generate_test_frame(self) -> bytes:
        """Génère un frame de test avec des informations de l'observateur."""
        if not Image:
            # Retourner des données de test simples si PIL n'est pas disponible
            return b'\x00' * (self.resolution[0] * self.resolution[1] * 3)
            
        width, height = self.resolution
        
        # Créer une image de test avec couleur basée sur la position
        x, y, z = self.position
        yaw, pitch = self.rotation
        
        # Générer une couleur basée sur la position
        r = int((x % 100) / 100 * 255)
        g = int((y % 100) / 100 * 255) 
        b = int((z % 100) / 100 * 255)
        
        # Créer l'image
        img = Image.new('RGB', (width, height), (r, g, b))
        
        # Ajouter du texte avec les informations de position
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            
            text_lines = [
                f"Observer: {self.observer_id}",
                f"Pos: ({x:.1f}, {y:.1f}, {z:.1f})",
                f"Rot: ({yaw:.1f}°, {pitch:.1f}°)",
                f"Time: {time.strftime('%H:%M:%S')}",
                "",
                "⚠ Mode Test Frame",
                "✓ Camera Active" if self.is_capturing else "✗ Camera Inactive",
                f"✓ 3D Rendering {'Available' if HAS_OPENGL else 'Unavailable'}",
                f"✓ World Model {'Set' if self.world_model else 'None'}"
            ]
            
            for i, line in enumerate(text_lines):
                if line:  # Skip empty lines
                    draw.text((10, 10 + i * 20), line, fill=(255, 255, 255))
                    
        except ImportError:
            pass  # Pas de texte si ImageDraw n'est pas disponible
            
        # Convertir en bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
            
        # Convertir en bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    def _render_3d_world_frame(self) -> bytes:
        """
        Rendu du monde 3D depuis la perspective de l'observateur.
        Inspiré des techniques de minecraft_client_fr.py
        """
        if not self._render_context or not HAS_FULL_GL:
            # Fallback vers frame de test si pas de contexte ou GL incomplet
            return self._generate_test_frame()
        
        try:
            # Activer le contexte de rendu pour cette caméra
            self._render_context.switch_to()
            
            # Configuration OpenGL pour le rendu 3D
            glClearColor(0.5, 0.69, 1.0, 1.0)  # Ciel bleu comme minecraft_client_fr.py
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)
            
            # Configuration de la projection perspective
            self._setup_3d_projection()
            
            # Configuration de la vue caméra
            self._setup_camera_view()
            
            # Rendu du monde (blocs)
            if hasattr(self.world_model, 'batch') and self.world_model.batch:
                glColor3f(1.0, 1.0, 1.0)  # Couleur neutre pour les blocs
                self.world_model.batch.draw()
            
            # Rendu des joueurs
            self._render_players()
            
            # Capture du framebuffer
            frame_data = self._capture_framebuffer()
            
            return frame_data
        except Exception as e:
            print(f"Erreur rendu 3D pour {self.observer_id}: {e}")
            return self._generate_test_frame()
    
    def _create_render_context(self):
        """Crée un contexte de rendu OpenGL headless pour cette caméra."""
        if not HAS_OPENGL:
            self._render_context = None
            return
            
        try:
            # Essayer de créer une fenêtre invisible pour le rendu
            # Configurer l'environnement pour le mode headless
            import os
            if not os.environ.get('DISPLAY'):
                print(f"Mode headless détecté pour caméra {self.observer_id}")
                self._render_context = None
                return
                
            self._render_context = pyglet.window.Window(
                width=self.resolution[0], 
                height=self.resolution[1],
                visible=False
            )
            print(f"Contexte rendu 3D créé pour caméra {self.observer_id}")
            
        except Exception as e:
            print(f"Impossible de créer contexte rendu pour {self.observer_id}: {e}")
            print(f"Caméra {self.observer_id} utilisera les frames de test")
            self._render_context = None
    
    def _setup_3d_projection(self):
        """Configure la projection 3D perspective."""
        width, height = self.resolution
        
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # Projection perspective similaire à minecraft_client_fr.py
        fov = 70.0  # Champ de vision par défaut
        aspect_ratio = width / float(height)
        near_plane = 0.1
        far_plane = 60.0
        
        # Try to use gluPerspective if available, otherwise fallback to manual matrix
        try:
            from OpenGL.GLU import gluPerspective
            gluPerspective(fov, aspect_ratio, near_plane, far_plane)
        except ImportError:
            # Calcul manuel de la perspective (sans gluPerspective)
            f = 1.0 / math.tan(math.radians(fov) / 2.0)
            
            perspective_matrix = [
                f / aspect_ratio, 0, 0, 0,
                0, f, 0, 0,
                0, 0, (far_plane + near_plane) / (near_plane - far_plane), -1,
                0, 0, (2 * far_plane * near_plane) / (near_plane - far_plane), 0
            ]
            
            # Use ctypes array to ensure proper format
            import ctypes
            matrix_array = (ctypes.c_float * 16)(*perspective_matrix)
            glMultMatrixf(matrix_array)
    
    def _setup_camera_view(self):
        """Configure la vue caméra depuis la position/rotation de l'observateur."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Récupérer position et rotation
        x, y, z = self.position
        yaw, pitch = self.rotation
        
        # Appliquer les rotations (inspiré de minecraft_client_fr.py)
        glRotatef(yaw, 0, 1, 0)    # Rotation horizontale (yaw)
        glRotatef(-pitch, math.cos(math.radians(yaw)), 0, math.sin(math.radians(yaw)))  # Rotation verticale (pitch)
        
        # Position de la caméra
        glTranslatef(-x, -y, -z)
    
    def _render_players(self):
        """Rendu des joueurs visibles dans le monde."""
        if not hasattr(self.world_model, 'other_players'):
            return
            
        # Rendu des autres joueurs comme cubes colorés
        for player_id, player in self.world_model.other_players.items():
            if hasattr(player, 'get_render_position'):
                try:
                    px, py, pz = player.get_render_position()
                    size = getattr(player, 'size', 0.5)
                    
                    # Couleur unique pour chaque joueur
                    color = self._get_player_color(player_id)
                    glColor3f(*color)
                    
                    # Rendu du cube joueur (simplifié)
                    self._render_cube(px, py, pz, size)
                    
                except Exception as e:
                    continue  # Ignorer les erreurs de rendu de joueurs individuels
    
    def _get_player_color(self, player_id):
        """Génère une couleur unique et stable pour un joueur."""
        if not hasattr(self, '_player_colors'):
            self._player_colors = {}
            
        if player_id not in self._player_colors:
            import hashlib
            hash_hex = hashlib.md5(player_id.encode()).hexdigest()
            
            r = int(hash_hex[0:2], 16) / 255.0
            g = int(hash_hex[2:4], 16) / 255.0  
            b = int(hash_hex[4:6], 16) / 255.0
            
            # Assurer une luminosité minimum
            brightness = (r + g + b) / 3
            if brightness < 0.5:
                factor = 0.7 / brightness
                r, g, b = min(1.0, r * factor), min(1.0, g * factor), min(1.0, b * factor)
                
            self._player_colors[player_id] = (r, g, b)
            
        return self._player_colors[player_id]
    
    def _render_cube(self, x, y, z, size):
        """Rendu d'un cube simple à la position donnée."""
        # Sommets d'un cube centré
        vertices = [
            # Face avant
            x-size, y-size, z+size,
            x+size, y-size, z+size,
            x+size, y+size, z+size,
            x-size, y+size, z+size,
            # Face arrière
            x-size, y-size, z-size,
            x-size, y+size, z-size,
            x+size, y+size, z-size,
            x+size, y-size, z-size,
            # ... autres faces
        ]
        
        # Rendu simplifié avec GL_QUADS
        glBegin(GL_QUADS)
        # Face avant
        glVertex3f(x-size, y-size, z+size)
        glVertex3f(x+size, y-size, z+size)
        glVertex3f(x+size, y+size, z+size)
        glVertex3f(x-size, y+size, z+size)
        # Face arrière  
        glVertex3f(x+size, y-size, z-size)
        glVertex3f(x-size, y-size, z-size)
        glVertex3f(x-size, y+size, z-size)
        glVertex3f(x+size, y+size, z-size)
        # Face droite
        glVertex3f(x+size, y-size, z+size)
        glVertex3f(x+size, y-size, z-size)
        glVertex3f(x+size, y+size, z-size)
        glVertex3f(x+size, y+size, z+size)
        # Face gauche
        glVertex3f(x-size, y-size, z-size)
        glVertex3f(x-size, y-size, z+size)
        glVertex3f(x-size, y+size, z+size)
        glVertex3f(x-size, y+size, z-size)
        # Face haut
        glVertex3f(x-size, y+size, z+size)
        glVertex3f(x+size, y+size, z+size)
        glVertex3f(x+size, y+size, z-size)
        glVertex3f(x-size, y+size, z-size)
        # Face bas
        glVertex3f(x-size, y-size, z-size)
        glVertex3f(x+size, y-size, z-size)
        glVertex3f(x+size, y-size, z+size)
        glVertex3f(x-size, y-size, z+size)
        glEnd()
    
    def _capture_framebuffer(self) -> bytes:
        """Capture le contenu du framebuffer OpenGL actuel."""
        width, height = self.resolution
        
        # Lire les pixels depuis le framebuffer
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        
        if not Image:
            # Retourner les pixels bruts si PIL n'est pas disponible
            return pixels
        
        # Convertir en image PIL et encoder en JPEG
        img = Image.frombytes('RGB', (width, height), pixels)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL a l'origine en bas à gauche
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
        
    def get_latest_frame(self) -> Optional[dict]:
        """Récupère le frame le plus récent."""
        with self.buffer_lock:
            if self.frame_buffer:
                return self.frame_buffer[-1]
            return None
            
    def get_frame_buffer(self) -> List[dict]:
        """Récupère tous les frames du buffer."""
        with self.buffer_lock:
            return self.frame_buffer.copy()
            
    def update_position(self, position: Tuple[float, float, float], 
                       rotation: Tuple[float, float] = None):
        """Met à jour la position/rotation de l'observateur."""
        self.position = position
        if rotation is not None:
            self.rotation = rotation


class ObserverCameraManager:
    """Gestionnaire des caméras d'observateurs."""
    
    def __init__(self):
        self.cameras = {}
        self.world_model = None
        
    def set_world_model(self, world_model):
        """Définit le modèle du monde pour le rendu."""
        self.world_model = world_model
        
    def create_camera(self, observer_id: str, position: Tuple[float, float, float],
                     rotation: Tuple[float, float], resolution: Tuple[int, int] = (640, 480)) -> ObserverCamera:
        """Crée une nouvelle caméra d'observateur."""
        camera = ObserverCamera(observer_id, position, rotation, resolution)
        self.cameras[observer_id] = camera
        
        if self.world_model:
            camera.start_capture(self.world_model)
            
        return camera
        
    def remove_camera(self, observer_id: str):
        """Supprime une caméra d'observateur."""
        if observer_id in self.cameras:
            self.cameras[observer_id].stop_capture()
            del self.cameras[observer_id]
            
    def get_camera(self, observer_id: str) -> Optional[ObserverCamera]:
        """Récupère une caméra par son ID."""
        return self.cameras.get(observer_id)
        
    def get_all_cameras(self) -> List[ObserverCamera]:
        """Récupère toutes les caméras."""
        return list(self.cameras.values())
        
    def start_all_cameras(self):
        """Démarre toutes les caméras."""
        if not self.world_model:
            print("Warning: Pas de modèle du monde défini pour les caméras")
            return
            
        for camera in self.cameras.values():
            camera.start_capture(self.world_model)
            
    def stop_all_cameras(self):
        """Arrête toutes les caméras."""
        for camera in self.cameras.values():
            camera.stop_capture()
            
    def update_camera_position(self, observer_id: str, position: Tuple[float, float, float],
                              rotation: Tuple[float, float] = None):
        """Met à jour la position d'une caméra."""
        camera = self.cameras.get(observer_id)
        if camera:
            camera.update_position(position, rotation)


# Instance globale du gestionnaire de caméras
camera_manager = ObserverCameraManager()