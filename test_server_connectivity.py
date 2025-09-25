#!/usr/bin/env python3
"""
Script de test de connectivité pour le serveur FastAPI
Test script for FastAPI server connectivity
"""

import asyncio
import requests
import time
import logging
from fastapi_camera_server import fastapi_camera_server

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

async def test_server_connectivity():
    """Test la connectivité au serveur FastAPI."""
    
    print("🔧 Test de Connectivité du Serveur FastAPI")
    print("=" * 50)
    
    # Test 1: Vérifier si le port est disponible
    print("\n1. Vérification de la disponibilité du port...")
    host = "localhost"
    port = 8080
    
    if fastapi_camera_server.is_port_available(host, port):
        print(f"✅ Port {port} disponible sur {host}")
    else:
        print(f"❌ Port {port} occupé sur {host}")
        print("   Vérification des processus utilisant le port:")
        import subprocess
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if f':{port}' in line:
                    print(f"   {line}")
        except Exception as e:
            print(f"   Erreur lors de la vérification: {e}")
        return False
    
    # Test 2: Démarrer le serveur en arrière-plan
    print("\n2. Démarrage du serveur en arrière-plan...")
    
    # Créer quelques caméras de test
    from observer_camera import camera_manager
    from user_manager import user_manager
    
    # Créer des utilisateurs de test
    users = user_manager.create_startup_users()
    print(f"   Créé {len(users)} utilisateurs de test")
    
    # Démarrer les caméras
    await user_manager.start_camera_server()
    print("   Caméras initialisées")
    
    # Démarrer le serveur en arrière-plan
    server_task = asyncio.create_task(fastapi_camera_server.start_server())
    
    # Attendre que le serveur démarre
    print("   Attente du démarrage du serveur...")
    await asyncio.sleep(3)
    
    # Test 3: Vérifier la connectivité
    print("\n3. Test de connectivité...")
    
    try:
        # Test du health check
        response = requests.get(f"http://{host}:{port}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check OK: {health_data['status']}")
            print(f"   Caméras totales: {health_data['cameras_total']}")
            print(f"   Caméras actives: {health_data['cameras_active']}")
        else:
            print(f"❌ Health check échoué: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    
    # Test 4: Test des endpoints principaux
    print("\n4. Test des endpoints...")
    
    endpoints = [
        ("/", "Interface web"),
        ("/cameras", "Liste des caméras"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://{host}:{port}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Erreur - {e}")
    
    # Test 5: Test curl simulation
    print("\n5. Simulation de curl...")
    try:
        import subprocess
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'http://{host}:{port}/'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip() == '200':
            print("✅ curl simulation: OK")
        else:
            print(f"❌ curl simulation: Code {result.stdout.strip()}")
            
    except Exception as e:
        print(f"❌ curl simulation: Erreur - {e}")
    
    print("\n🎉 Tests de connectivité terminés!")
    print(f"🌐 Serveur accessible sur: http://{host}:{port}")
    print("   Appuyez sur Ctrl+C pour arrêter")
    
    # Garder le serveur en marche pour les tests manuels
    try:
        await server_task
    except asyncio.CancelledError:
        print("\n⏹️  Serveur arrêté")
    
    return True

async def main():
    """Point d'entrée principal."""
    try:
        await test_server_connectivity()
    except KeyboardInterrupt:
        print("\n⏹️  Test arrêté par l'utilisateur")
    except Exception as e:
        logging.error(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())