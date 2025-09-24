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
try:
    import pyglet
    from pyglet.gl import *
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False
    print("Warning: OpenGL/Pyglet not available, using headless mode")

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
        Pour l'instant, génère un frame de test coloré.
        """
        # Pour l'instant, générer une image de test avec des informations
        # de position/rotation de l'observateur
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
                f"Time: {time.strftime('%H:%M:%S')}"
            ]
            
            for i, line in enumerate(text_lines):
                draw.text((10, 10 + i * 20), line, fill=(255, 255, 255))
                
        except ImportError:
            pass  # Pas de texte si ImageDraw n'est pas disponible
            
        # Convertir en bytes
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