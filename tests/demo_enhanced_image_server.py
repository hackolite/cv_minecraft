#!/usr/bin/env python3
"""
Démonstration du serveur d'images Minecraft amélioré
====================================================

Ce script démontre les nouvelles fonctionnalités inspirées de mini_minecraft_pyglet_server_corrected.py:
- Capture d'images automatique et mise en cache  
- Endpoint /view pour les images mises en cache (plus rapide)
- Endpoint /get_view pour les captures immédiates
- Support du mode headless avec images de test

Usage:
    python3 demo_enhanced_image_server.py
"""

import requests
import time
import sys
import threading
import subprocess
from PIL import Image
import io

def test_image_server():
    """Test du serveur d'images amélioré."""
    
    print("🎮 Démonstration du serveur d'images Minecraft amélioré")
    print("=" * 60)
    print()
    
    # Configuration
    port = 8085
    base_url = f"http://127.0.0.1:{port}"
    
    # Démarrer le serveur minecraft client en arrière-plan
    print("🚀 Démarrage du serveur Minecraft...")
    
    server_process = subprocess.Popen([
        sys.executable, "minecraft_client.py", 
        "--headless", 
        f"--server-port={port}",
        "--capture-interval=0.5"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Attendre que le serveur démarre
    print("⏳ Attente du démarrage du serveur...")
    time.sleep(5)
    
    try:
        # Test 1: Vérifier le statut
        print("\n📊 Test 1: Vérification du statut")
        print("-" * 30)
        
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Serveur actif")
            print(f"   - Auto-capture: {status.get('auto_capture')}")
            print(f"   - Intervalle: {status.get('capture_interval')}s")
            print(f"   - Image en cache: {status.get('has_cached_image')}")
            print(f"   - Position: {status.get('position')}")
        else:
            print(f"❌ Erreur statut: {response.status_code}")
            return
        
        # Test 2: Test de l'endpoint /view (cached)
        print("\n🖼️  Test 2: Endpoint /view (image mise en cache)")
        print("-" * 50)
        
        response = requests.get(f"{base_url}/view")
        if response.status_code == 200:
            if response.headers.get('content-type') == 'image/png':
                # Sauvegarder l'image
                with open('/tmp/demo_cached_view.png', 'wb') as f:
                    f.write(response.content)
                
                # Analyser l'image
                img = Image.open(io.BytesIO(response.content))
                print(f"✅ Image reçue avec succès")
                print(f"   - Taille: {img.size}")
                print(f"   - Mode: {img.mode}")
                print(f"   - Fichier sauvé: /tmp/demo_cached_view.png")
            else:
                print(f"❌ Type de contenu inattendu: {response.headers.get('content-type')}")
        else:
            print(f"❌ Erreur /view: {response.status_code}")
        
        # Test 3: Test de l'endpoint /get_view (direct)
        print("\n📸 Test 3: Endpoint /get_view (capture directe)")
        print("-" * 50)
        
        response = requests.get(f"{base_url}/get_view")
        if response.status_code == 200:
            if response.headers.get('content-type') == 'image/png':
                with open('/tmp/demo_direct_view.png', 'wb') as f:
                    f.write(response.content)
                
                img = Image.open(io.BytesIO(response.content))
                print(f"✅ Capture directe réussie")
                print(f"   - Taille: {img.size}")
                print(f"   - Mode: {img.mode}")
                print(f"   - Fichier sauvé: /tmp/demo_direct_view.png")
            else:
                print(f"❌ Type de contenu inattendu: {response.headers.get('content-type')}")
        else:
            # En mode headless, c'est normal que /get_view échoue
            print(f"ℹ️  Capture directe non disponible en mode headless (attendu): {response.status_code}")
            try:
                error = response.json()
                print(f"   - Message: {error.get('detail')}")
            except:
                pass
        
        # Test 4: Attendre et vérifier la mise à jour du cache
        print("\n⏱️  Test 4: Vérification de la mise à jour automatique du cache")
        print("-" * 60)
        
        print("⏳ Attente de 2 secondes pour la mise à jour du cache...")
        time.sleep(2)
        
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"📊 Image en cache après attente: {status.get('has_cached_image')}")
        
        # Test 5: Comparaison des performances
        print("\n⚡ Test 5: Comparaison des performances")
        print("-" * 40)
        
        # Test /view (cached)
        start_time = time.time()
        response = requests.get(f"{base_url}/view")
        cached_time = time.time() - start_time
        
        print(f"📊 Endpoint /view (cached): {cached_time:.3f}s")
        
        # Test /get_view (direct) - peut échouer en headless
        start_time = time.time()
        response = requests.get(f"{base_url}/get_view")
        direct_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"📊 Endpoint /get_view (direct): {direct_time:.3f}s")
            print(f"🚀 Gain de performance: {direct_time/cached_time:.1f}x plus rapide avec cache")
        else:
            print(f"📊 Endpoint /get_view (direct): Non disponible en headless")
        
        print("\n🎉 Tests terminés avec succès!")
        print(f"📁 Images sauvées dans /tmp/demo_*.png")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        # Arrêter le serveur
        print("\n🛑 Arrêt du serveur...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()
        print("✅ Serveur arrêté")

def main():
    """Point d'entrée principal."""
    try:
        test_image_server()
    except KeyboardInterrupt:
        print("\n🛑 Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()