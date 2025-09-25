#!/usr/bin/env python3
"""
Démonstration du système de caméras FastAPI
FastAPI Camera System Demonstration

Ce script démontre le nouveau système de caméras avec interface web FastAPI.
"""

import asyncio
import logging
import time
from user_manager import user_manager
from observer_camera import camera_manager
from fastapi_camera_server import fastapi_camera_server

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

async def demo_fastapi_cameras():
    """Démonstration du système de caméras FastAPI."""
    
    print("🎬 Démonstration du Système de Caméras FastAPI")
    print("=" * 60)
    print()
    
    # Créer les utilisateurs et caméras
    print("📡 Création des observateurs...")
    users = user_manager.create_startup_users()
    
    for user in users:
        print(f"✅ {user.name} créé à la position {user.position}")
    
    print()
    
    # Démarrer le système de caméras
    print("🚀 Démarrage du système de caméras...")
    await user_manager.start_camera_server()
    
    print("✅ Système de caméras démarré!")
    print()
    
    # Afficher les informations de connexion
    print("📺 URLs de Streaming Disponibles:")
    print("-" * 40)
    web_url = user_manager.get_web_interface_url()
    print(f"🌐 Interface Web: {web_url}")
    print()
    
    camera_urls = user_manager.get_camera_urls()
    for name, url in camera_urls.items():
        print(f"🎥 {name}: {url}")
    
    print()
    print("💡 Pour tester le streaming:")
    print("   # Interface web (recommandé):")
    print(f"   {web_url}")
    print()
    print("   # URLs individuelles:")
    for name, url in camera_urls.items():
        print(f"   {name}: {url}")
    print()
    print("   # API REST:")
    print(f"   GET {web_url}cameras - Liste des caméras")
    print(f"   GET {web_url}camera/{{id}}/image - Image individuelle")
    print(f"   GET {web_url}camera/{{id}}/stream - Stream MJPEG")
    print()
    
    # Attendre et montrer l'activité des caméras
    print("⏱️  Vérification de l'activité des caméras...")
    await asyncio.sleep(3)
    
    active_cameras = 0
    for camera in camera_manager.get_all_cameras():
        if camera.is_capturing:
            active_cameras += 1
            frame = camera.get_latest_frame()
            if frame:
                print(f"✅ {camera.observer_id}: Frame capturé ({len(frame['data'])} bytes)")
            else:
                print(f"⚠️  {camera.observer_id}: Pas de frame disponible")
        else:
            print(f"❌ {camera.observer_id}: Caméra inactive")
    
    print(f"\n📊 Résumé: {active_cameras}/{len(camera_manager.get_all_cameras())} caméras actives")
    
    print()
    print("🎉 Démonstration terminée!")
    print("📝 Note: Le serveur FastAPI continue de tourner en arrière-plan")
    print("   Pour le tester, allez sur:", web_url)


async def main():
    """Point d'entrée principal."""
    try:
        await demo_fastapi_cameras()
        
        # Démarrer le serveur FastAPI et attendre
        print("\n🚀 Démarrage du serveur FastAPI...")
        print("Accédez à http://localhost:8080 pour voir l'interface web")
        print("Appuyez sur Ctrl+C pour arrêter")
        print()
        
        # Afficher les informations de diagnostic
        print("💡 En cas de problème de connexion:")
        print("   - Utilisez: python server_health_check.py")
        print("   - Vérifiez les logs ci-dessus pour des erreurs")
        print("   - Le serveur peut prendre quelques secondes à démarrer")
        print()
        
        # Démarrer le serveur avec gestion d'erreur améliorée
        try:
            await fastapi_camera_server.start_server()
        except Exception as e:
            print(f"\n❌ Erreur lors du démarrage du serveur: {e}")
            print("\n🔧 Diagnostic automatique:")
            
            # Importer et exécuter le diagnostic
            try:
                import server_health_check
                server_health_check.main()
            except Exception:
                print("   Impossible d'exécuter le diagnostic automatique")
                print("   Exécutez manuellement: python server_health_check.py")
            
            raise
        
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du serveur...")
        await user_manager.stop_camera_server()
    except Exception as e:
        logging.error(f"Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())