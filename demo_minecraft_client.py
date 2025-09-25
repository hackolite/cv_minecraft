#!/usr/bin/env python3
"""
Démonstration du Client Minecraft Abstrait
==========================================

Ce script montre comment utiliser la nouvelle classe MinecraftClient
pour créer un client Minecraft contrôlable via API FastAPI.

Usage:
    # Mode GUI (pour jouer normalement)
    python3 demo_minecraft_client.py --gui
    
    # Mode headless (serveur API seulement)
    python3 demo_minecraft_client.py --headless
    
    # Configuration personnalisée
    python3 demo_minecraft_client.py --position 100 150 100 --block-type BRICK --port 8080
"""

import sys
import argparse
import time
import requests
import threading
from minecraft_client import MinecraftClient

def demo_api_calls():
    """Démontre l'utilisation de l'API après 8 secondes.""" 
    time.sleep(8)  # Attendre plus longtemps pour que le serveur soit prêt
    
    print("\n" + "="*50)
    print("🤖 Démonstration de l'API FastAPI")
    print("="*50)
    
    base_url = "http://localhost:8080"
    
    try:
        # Test du statut
        print("📊 Status du client:")
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Running: {data['running']}")
            print(f"   - Position: {data['position']}")
            print(f"   - Flying: {data.get('flying', False)}")
            print(f"   - World blocks: {data.get('world_blocks', 0)}")
        
        # Test de téléportation
        print("\n🚀 Téléportation à (200, 100, 200):")
        response = requests.post(f"{base_url}/teleport", params={"x": 200, "y": 100, "z": 200})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data['message']}")
            print(f"   - Nouvelle position: {data['position']}")
        else:
            print(f"   ❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")
        
        # Test de mouvement relatif
        print("\n🏃 Mouvement relatif (+10, +5, -5):")
        response = requests.post(f"{base_url}/move", params={"dx": 10, "dy": 5, "dz": -5})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data['message']}")
            print(f"   - Position précédente: {data['previous_position']}")
            print(f"   - Nouvelle position: {data['new_position']}")
        else:
            print(f"   ❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")
        
        # Test de placement de bloc
        print("\n🧱 Placement d'un bloc STONE à (210, 100, 210):")
        response = requests.post(f"{base_url}/place_block", 
                               params={"x": 210, "y": 100, "z": 210, "block_type": "STONE"})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data['message']}")
            print(f"   - Bloc: {data['block_type']} à {data['position']}")
        else:
            print(f"   ❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")
        
        # Test de suppression de bloc  
        print("\n🗑️  Suppression du bloc à (210, 100, 210):")
        response = requests.post(f"{base_url}/remove_block", params={"x": 210, "y": 100, "z": 210})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data['message']}")
            print(f"   - Position: {data['position']}")
        else:
            print(f"   ❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")
        
        # Test de capture d'écran (si GUI actif)
        print("\n📸 Test de capture d'écran:")
        response = requests.get(f"{base_url}/get_view")
        if response.status_code == 200:
            print(f"   ✅ Capture réussie ({len(response.content)} bytes)")
            # Sauvegarder l'image pour test
            with open("/tmp/minecraft_view.png", "wb") as f:
                f.write(response.content)
            print("   📁 Image sauvée: /tmp/minecraft_view.png")
        else:
            print(f"   ⚠️  Capture non disponible: {response.json().get('detail', 'Mode headless')}")
        
        print("\n✅ Démonstration API terminée!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API. Le serveur est-il démarré?")
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration API: {e}")

def main():
    parser = argparse.ArgumentParser(description="Démonstration du Client Minecraft Abstrait")
    parser.add_argument('--gui', action='store_true', help='Mode GUI (interface graphique)')
    parser.add_argument('--headless', action='store_true', help='Mode headless (serveur API seulement)')
    parser.add_argument('--position', nargs=3, type=float, default=[50, 80, 50],
                       help='Position de départ [x y z]')
    parser.add_argument('--block-type', default='GRASS', 
                       help='Type de bloc par défaut (GRASS, STONE, SAND, BRICK)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port du serveur FastAPI')
    parser.add_argument('--demo-api', action='store_true',
                       help='Exécuter une démonstration des appels API')
    
    args = parser.parse_args()
    
    # Déterminer le mode
    if args.gui and args.headless:
        print("❌ Erreur: --gui et --headless sont mutuellement exclusifs")
        return 1
    
    enable_gui = args.gui or not args.headless  # GUI par défaut sauf si --headless
    
    print("🎮 Démonstration du Client Minecraft Abstrait")
    print("=" * 50)
    print(f"Mode: {'GUI' if enable_gui else 'Headless'}")
    print(f"Position: {args.position}")
    print(f"Bloc par défaut: {args.block_type}")
    print(f"Port API: {args.port}")
    
    # Créer le client
    client = MinecraftClient(
        position=tuple(args.position),
        block_type=args.block_type,
        server_host="localhost",
        server_port=args.port,
        enable_gui=enable_gui
    )
    
    # Démarrer le serveur API
    print("\n🚀 Démarrage du serveur API...")
    success = client.start_server()
    if not success:
        print("❌ Échec du démarrage du serveur API")
        return 1
    
    # Démarrer la démonstration API si demandée
    if args.demo_api:
        demo_thread = threading.Thread(target=demo_api_calls, daemon=True)
        demo_thread.start()
    
    # Instructions pour l'utilisateur
    print(f"\n🌐 API disponible sur: http://localhost:{args.port}")
    print(f"📚 Documentation: http://localhost:{args.port}/docs")
    
    if enable_gui:
        print("\n🎮 Instructions GUI:")
        print("  - WASD/ZQSD : Se déplacer")
        print("  - Espace : Sauter/Voler vers le haut")
        print("  - Shift : S'accroupir/Voler vers le bas")
        print("  - Clic droit : Placer un bloc")
        print("  - Clic gauche : Détruire un bloc")
        print("  - Tab : Afficher/masquer les informations debug")
        print("  - F : Activer/désactiver le vol")
    else:
        print("\n🤖 Mode Headless:")
        print("  - Utilisez l'API pour contrôler le client")
        print("  - Ctrl+C pour arrêter")
    
    print("\n💡 Exemples d'appels API:")
    print(f"  curl http://localhost:{args.port}/status")
    print(f"  curl -X POST 'http://localhost:{args.port}/teleport?x=100&y=50&z=100'")
    print(f"  curl -X POST 'http://localhost:{args.port}/move?dx=10&dy=0&dz=5'")
    print(f"  curl -X POST 'http://localhost:{args.port}/place_block?x=101&y=50&z=101&block_type=STONE'")
    
    # Lancer le client
    try:
        print("\n" + "="*50)
        client.run()
    except KeyboardInterrupt:
        print("\n👋 Client arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())