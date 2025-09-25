#!/usr/bin/env python3
"""
Camera Viewer - Visualiseur de Caméras Minecraft
===============================================

Ce script permet de visualiser ce que voient les caméras créées dans le monde Minecraft
en interrogeant leurs endpoints FastAPI individuels.

Usage:
    python3 camera_viewer.py --list                    # Liste toutes les caméras
    python3 camera_viewer.py --camera <id>             # Affiche une caméra spécifique
    python3 camera_viewer.py --position 10 50 20       # Affiche la caméra à cette position
    python3 camera_viewer.py --save <filename.png>     # Sauvegarde l'image
"""

import argparse
import requests
import json
import sys
import time
from typing import List, Dict, Optional
from pathlib import Path

from camera_user_manager import camera_manager

def list_cameras() -> List[Dict]:
    """Liste toutes les caméras actives."""
    try:
        cameras = camera_manager.get_cameras()
        return cameras
    except Exception as e:
        print(f"Erreur lors de la récupération des caméras: {e}")
        return []

def get_camera_view(camera_url: str, save_path: Optional[str] = None) -> bool:
    """Récupère et affiche/sauvegarde la vue d'une caméra."""
    try:
        view_url = f"{camera_url}/get_view"
        print(f"Récupération de la vue depuis: {view_url}")
        
        response = requests.get(view_url, timeout=10)
        response.raise_for_status()
        
        if save_path:
            # Sauvegarder l'image
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"Image sauvegardée: {save_path}")
        else:
            # Afficher des informations sur l'image
            print(f"Vue récupérée avec succès ({len(response.content)} bytes)")
            print(f"Type de contenu: {response.headers.get('content-type', 'unknown')}")
            
            # Essayer de sauvegarder temporairement pour l'affichage
            temp_path = f"/tmp/camera_view_{int(time.time())}.png"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            print(f"Image temporaire créée: {temp_path}")
            
            # Essayer d'ouvrir l'image avec un visualiseur système
            try:
                import subprocess
                import shutil
                
                # Essayer différents visualiseurs d'images
                viewers = ['eog', 'display', 'feh', 'xdg-open']
                for viewer in viewers:
                    if shutil.which(viewer):
                        subprocess.run([viewer, temp_path], check=False)
                        print(f"Image ouverte avec {viewer}")
                        break
                else:
                    print("Aucun visualiseur d'image trouvé. Image sauvegardée temporairement.")
                    
            except Exception as e:
                print(f"Impossible d'ouvrir l'image automatiquement: {e}")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"Timeout lors de la connexion à {camera_url}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Impossible de se connecter à {camera_url}")
        print("Vérifiez que la caméra est active et accessible")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP: {e}")
        return False
    except Exception as e:
        print(f"Erreur lors de la récupération de la vue: {e}")
        return False

def find_camera_by_position(cameras: List[Dict], position: tuple) -> Optional[Dict]:
    """Trouve une caméra à une position donnée."""
    for camera in cameras:
        if tuple(camera['position']) == position:
            return camera
    return None

def find_camera_by_id(cameras: List[Dict], camera_id: str) -> Optional[Dict]:
    """Trouve une caméra par son ID."""
    for camera in cameras:
        if camera['id'] == camera_id:
            return camera
    return None

def test_camera_connectivity(camera: Dict) -> bool:
    """Test la connectivité d'une caméra."""
    try:
        response = requests.get(camera['url'], timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Visualiseur de caméras Minecraft")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='Liste toutes les caméras')
    group.add_argument('--camera', type=str, help='ID de la caméra à visualiser')
    group.add_argument('--position', nargs=3, type=int, metavar=('X', 'Y', 'Z'), 
                      help='Position de la caméra à visualiser')
    
    parser.add_argument('--save', type=str, help='Chemin pour sauvegarder l\'image')
    parser.add_argument('--test', action='store_true', help='Test la connectivité des caméras')
    
    args = parser.parse_args()
    
    # Récupérer la liste des caméras
    cameras = list_cameras()
    
    if args.list:
        print("=== Caméras Actives ===")
        if not cameras:
            print("Aucune caméra active trouvée.")
            print("\nPour créer une caméra:")
            print("1. Connectez-vous au serveur Minecraft")
            print("2. Sélectionnez le bloc CAMERA (touche 5)")
            print("3. Placez le bloc où vous voulez la caméra")
            return
        
        for i, camera in enumerate(cameras, 1):
            status = "🟢" if camera['running'] else "🔴"
            connectivity = ""
            if args.test:
                connectivity = " 🔗" if test_camera_connectivity(camera) else " ❌"
            
            print(f"{i}. {status} {camera['id']}{connectivity}")
            print(f"   Position: {camera['position']}")
            print(f"   Port: {camera['port']}")
            print(f"   URL: {camera['url']}")
            print(f"   Vue: {camera['view_endpoint']}")
            print()
        
        return
    
    if not cameras:
        print("Aucune caméra active trouvée.")
        print("Placez des blocs CAMERA dans le monde pour créer des caméras.")
        return 1
    
    # Trouver la caméra cible
    target_camera = None
    
    if args.camera:
        target_camera = find_camera_by_id(cameras, args.camera)
        if not target_camera:
            print(f"Caméra '{args.camera}' non trouvée.")
            print("Caméras disponibles:")
            for camera in cameras:
                print(f"  - {camera['id']}")
            return 1
    
    elif args.position:
        position = tuple(args.position)
        target_camera = find_camera_by_position(cameras, position)
        if not target_camera:
            print(f"Aucune caméra trouvée à la position {position}.")
            print("Positions des caméras disponibles:")
            for camera in cameras:
                print(f"  - {camera['position']} ({camera['id']})")
            return 1
    
    if not target_camera:
        print("Erreur: aucune caméra sélectionnée.")
        return 1
    
    # Récupérer et afficher la vue de la caméra
    print(f"=== Vue de la caméra {target_camera['id']} ===")
    print(f"Position: {target_camera['position']}")
    print(f"État: {'actif' if target_camera['running'] else 'inactif'}")
    print()
    
    if not target_camera['running']:
        print("⚠️  La caméra n'est pas active. Elle pourrait ne pas répondre.")
    
    success = get_camera_view(target_camera['url'], args.save)
    
    if not success:
        print("\nDépannage:")
        print("1. Vérifiez que le serveur Minecraft est en cours d'exécution")
        print("2. Vérifiez que la caméra est bien créée et active")
        print("3. Essayez d'attendre quelques secondes et de relancer")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())