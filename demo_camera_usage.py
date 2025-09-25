#!/usr/bin/env python3
"""
Demo Camera Usage - Démo d'utilisation des caméras
=================================================

Ce script montre comment:
1. Créer des caméras
2. Lister les caméras disponibles
3. Récupérer la vue d'une caméra
"""

import time
from camera_user_manager import camera_manager

def demo_camera_system():
    """Démo du système de caméras."""
    print("=" * 60)
    print("🎬 DÉMO D'UTILISATION DES CAMÉRAS MINECRAFT")
    print("=" * 60)
    
    # Nettoyer les caméras existantes
    print("🧹 Nettoyage des caméras existantes...")
    for camera_id in list(camera_manager.cameras.keys()):
        camera = camera_manager.cameras[camera_id]
        camera_manager.remove_camera_user(camera.position)
    
    # 1. Créer quelques caméras
    print("\n📹 Création de caméras de test...")
    test_positions = [
        (50, 60, 50),
        (60, 60, 50), 
        (50, 60, 60)
    ]
    
    created_cameras = []
    for i, position in enumerate(test_positions):
        print(f"   Création caméra {i+1} à {position}...")
        camera = camera_manager.create_camera_user(position)
        if camera:
            created_cameras.append(camera)
            print(f"   ✅ Caméra {camera.id} créée sur le port {camera.port}")
        else:
            print(f"   ❌ Échec création caméra à {position}")
    
    # Attendre que les serveurs démarrent
    print("\n⏳ Attente du démarrage des serveurs...")
    time.sleep(3)
    
    # 2. Lister les caméras
    print("\n📋 Liste des caméras actives:")
    cameras = camera_manager.get_cameras()
    if cameras:
        for i, camera in enumerate(cameras, 1):
            status = "🟢" if camera['running'] else "🔴"
            print(f"   {i}. {status} {camera['id']}")
            print(f"      Position: {camera['position']}")
            print(f"      Port: {camera['port']}")
            print(f"      URL: {camera['url']}")
            print(f"      Vue: {camera['view_endpoint']}")
            print()
    else:
        print("   Aucune caméra trouvée")
    
    # 3. Démonstration d'utilisation
    if cameras:
        print("📖 Exemples d'utilisation:")
        print("   # Lister toutes les caméras")
        print("   python3 camera_viewer.py --list")
        print()
        
        # Montrer un exemple pour chaque caméra
        for camera in cameras:
            print(f"   # Voir la caméra {camera['id']}")
            print(f"   python3 camera_viewer.py --camera {camera['id']}")
            print(f"   python3 camera_viewer.py --position {camera['position'][0]} {camera['position'][1]} {camera['position'][2]}")
            print()
    
    # 4. Dans un vrai usage Minecraft
    print("🎮 Dans un vrai serveur Minecraft:")
    print("   1. Lancez le serveur: python3 server.py")
    print("   2. Connectez un client: python3 minecraft_client_fr.py")
    print("   3. Sélectionnez le bloc CAMERA (touche 5)")
    print("   4. Placez le bloc où vous voulez une caméra")
    print("   5. Utilisez camera_viewer.py pour voir ce que voit la caméra")
    
    # Nettoyage
    print("\n🧹 Nettoyage final...")
    for camera in created_cameras:
        camera_manager.remove_camera_user(camera.position)
        print(f"   ✅ Caméra {camera.id} supprimée")
    
    print("\n🎉 Démo terminée avec succès!")

if __name__ == "__main__":
    demo_camera_system()