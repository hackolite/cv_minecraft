#!/usr/bin/env python3
"""
Exemple d'utilisation du Client Minecraft Abstrait
=================================================

Ce script montre différentes façons d'utiliser la classe MinecraftClient.
"""

from minecraft_client import MinecraftClient
import time
import requests
import threading

def example_1_basic_usage():
    """Exemple 1: Usage basique avec GUI"""
    print("🎮 Exemple 1: Client avec interface graphique")
    
    client = MinecraftClient(
        position=(0, 50, 0),
        block_type="STONE",
        server_port=8001
    )
    
    # Démarrer le serveur API
    client.start_server()
    
    print("Client prêt! API disponible sur http://localhost:8001")
    print("Fermez la fenêtre ou appuyez sur Ctrl+C pour continuer...")
    
    try:
        # En mode GUI, run() bloque jusqu'à fermeture de la fenêtre
        client.run()  
    except KeyboardInterrupt:
        print("Client interrompu")

def example_2_headless_control():
    """Exemple 2: Contrôle programmatique en mode headless"""
    print("\n🤖 Exemple 2: Contrôle programmatique (headless)")
    
    client = MinecraftClient(
        position=(100, 60, 100),
        block_type="BRICK",
        server_port=8002,
        enable_gui=False  # Mode headless
    )
    
    # Démarrer le serveur
    client.start_server()
    
    # Fonction pour contrôler le client via API
    def control_client():
        time.sleep(2)  # Attendre que le serveur démarre
        
        base_url = "http://localhost:8002"
        
        print("  📊 Statut initial:")
        response = requests.get(f"{base_url}/status")
        data = response.json()
        print(f"    Position: {data['position']}")
        
        print("  🚀 Téléportation à (200, 80, 200)...")
        requests.post(f"{base_url}/teleport", params={"x": 200, "y": 80, "z": 200})
        
        print("  🧱 Placement de 5 blocs en ligne...")
        for i in range(5):
            requests.post(f"{base_url}/place_block", 
                         params={"x": 200+i, "y": 80, "z": 201, "block_type": "BRICK"})
        
        print("  📊 Statut final:")
        response = requests.get(f"{base_url}/status")
        data = response.json()
        print(f"    Position: {data['position']}")
        print(f"    Blocs dans le monde: {data['world_blocks']}")
        
        print("  ✅ Contrôle terminé")
    
    # Lancer le contrôle dans un thread
    control_thread = threading.Thread(target=control_client, daemon=True)
    control_thread.start()
    
    # Lancer le client (boucle pendant 10 secondes en mode headless)
    print("  🔄 Client en cours d'exécution...")
    try:
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("  Client interrompu")

def example_3_mixed_mode():
    """Exemple 3: Mode mixte - GUI + contrôle API"""
    print("\n🎯 Exemple 3: Mode mixte (GUI + API)")
    
    client = MinecraftClient(
        position=(300, 70, 300),
        block_type="GRASS",
        server_host="localhost",
        server_port=8003,
        enable_gui=True
    )
    
    # Démarrer le serveur
    client.start_server()
    
    # Fonction pour démonstration API en parallèle
    def api_demo():
        time.sleep(5)  # Laisser le temps au joueur de voir le monde
        
        print("  🤖 Démonstration API pendant que vous jouez...")
        base_url = "http://localhost:8003"
        
        # Créer une structure automatiquement
        print("  🏗️  Construction d'une petite structure...")
        for x in range(3):
            for z in range(3):
                requests.post(f"{base_url}/place_block",
                             params={"x": 305+x, "y": 70, "z": 305+z, "block_type": "STONE"})
                time.sleep(0.1)
        
        print("  ✅ Structure créée via API!")
    
    # Lancer la démonstration API
    demo_thread = threading.Thread(target=api_demo, daemon=True)
    demo_thread.start()
    
    print("  🎮 Vous pouvez maintenant jouer normalement...")
    print("  🤖 L'API va construire une structure automatiquement")
    print("  📝 Fermez la fenêtre quand vous avez terminé")
    
    # Note: En pratique, vous appelleriez client.run() ici, 
    # mais pour la démonstration on simule juste
    print("  ⏳ [Simulation - en réalité le client graphique s'ouvrirait]")
    time.sleep(10)

def main():
    print("🔧 Exemples d'utilisation du Client Minecraft Abstrait")
    print("=" * 60)
    
    print("Choix disponibles:")
    print("1 - Client avec interface graphique")
    print("2 - Contrôle programmatique (headless)")  
    print("3 - Mode mixte (GUI + API)")
    print("0 - Quitter")
    
    while True:
        try:
            choice = input("\nVotre choix (0-3): ").strip()
            
            if choice == "0":
                print("👋 Au revoir!")
                break
            elif choice == "1":
                example_1_basic_usage()
            elif choice == "2":
                example_2_headless_control()
            elif choice == "3":
                example_3_mixed_mode()
            else:
                print("❌ Choix invalide, utilisez 0-3")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()