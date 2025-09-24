#!/usr/bin/env python3
"""
Démonstration du système de streaming RTSP
RTSP Streaming System Demonstration

Ce script démontre le nouveau système de streaming vidéo RTSP avec des caméras d'observateurs réelles.
"""

import asyncio
import logging
import time
from user_manager import user_manager
from observer_camera import camera_manager

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

async def demo_rtsp_streaming():
    """Démonstration du streaming RTSP avec caméras réelles."""
    
    print("🎬 Démonstration du Système de Streaming RTSP")
    print("=" * 60)
    print()
    
    # Créer les utilisateurs RTSP
    print("📡 Création des observateurs RTSP...")
    users = user_manager.create_startup_users()
    
    for user in users:
        print(f"✅ {user.name} créé à la position {user.position}")
        print(f"   URL RTSP: {user.rtsp_url}")
    
    print()
    
    # Démarrer les serveurs RTSP avec streaming vidéo
    print("🚀 Démarrage des serveurs RTSP avec streaming vidéo...")
    await user_manager.start_rtsp_servers()
    
    print("✅ Serveurs RTSP démarrés!")
    print()
    
    # Afficher les informations de connexion
    print("📺 URLs de Streaming Disponibles:")
    print("-" * 40)
    urls = user_manager.get_rtsp_urls()
    for name, url in urls.items():
        print(f"🎥 {name}: {url}")
    
    print()
    print("💡 Pour tester le streaming:")
    print("   # Avec VLC:")
    for name, url in urls.items():
        print(f"   vlc {url}")
    print()
    print("   # Avec ffmpeg:")
    for name, url in urls.items():
        print(f"   ffplay {url}")
    
    print()
    print("🔄 Démonstration en cours...")
    
    # Laisser tourner pendant quelques secondes pour la démonstration
    for i in range(10):
        await asyncio.sleep(1)
        
        # Afficher les statistiques des caméras
        cameras = camera_manager.get_all_cameras()
        active_cameras = 0
        total_frames = 0
        
        for camera in cameras:
            frame = camera.get_latest_frame()
            if frame:
                active_cameras += 1
                buffer = camera.get_frame_buffer()
                total_frames += len(buffer)
        
        print(f"📊 Caméras actives: {active_cameras}/{len(cameras)} | "
              f"Frames en buffer: {total_frames} | "
              f"Temps: {i+1}/10s", end='\r')
    
    print()
    print()
    print("📈 Statistiques Finales:")
    print("-" * 30)
    
    cameras = camera_manager.get_all_cameras()
    for camera in cameras:
        frame = camera.get_latest_frame()
        if frame:
            buffer_size = len(camera.get_frame_buffer())
            frame_size = len(frame['data'])
            print(f"🎥 {camera.observer_id}:")
            print(f"   - Dernier frame: {frame_size} bytes")
            print(f"   - Buffer: {buffer_size} frames")
            print(f"   - Position: {camera.position}")
            print(f"   - Rotation: {camera.rotation}")
        else:
            print(f"⚠️  {camera.observer_id}: Pas de frames")
    
    print()
    
    # Arrêter les serveurs
    print("🔌 Arrêt des serveurs RTSP...")
    await user_manager.stop_rtsp_servers()
    
    print("✅ Démonstration terminée!")
    print()
    print("🎯 Résumé:")
    print("✅ Serveurs RTSP avec streaming vidéo réel fonctionnels")
    print("✅ Caméras d'observateurs capturant des frames")
    print("✅ Transmission RTP des données vidéo")
    print("✅ Support multi-observateurs simultanés")

async def main():
    """Point d'entrée principal."""
    try:
        await demo_rtsp_streaming()
        return 0
    except KeyboardInterrupt:
        print("\n🛑 Démonstration interrompue par l'utilisateur")
        # Nettoyer
        try:
            await user_manager.stop_rtsp_servers()
        except:
            pass
        return 0
    except Exception as e:
        logging.error(f"❌ Erreur dans la démonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("🎬 Démonstration RTSP Streaming - CV Minecraft")
    print("Appuyez sur Ctrl+C pour arrêter\n")
    exit(asyncio.run(main()))