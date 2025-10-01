#!/usr/bin/env python3
"""
Exemple d'utilisation du Client Minecraft Abstrait
=================================================

Ce script montre différentes façons d'utiliser la classe MinecraftClient.
"""

from minecraft_client import MinecraftClient
import time

def example_1_basic_usage():
    """Exemple 1: Usage basique avec GUI"""
    print("🎮 Exemple 1: Client avec interface graphique")
    
    client = MinecraftClient(
        position=(0, 50, 0),
        block_type="STONE"
    )
    
    print("Client prêt!")
    print("Fermez la fenêtre ou appuyez sur Ctrl+C pour continuer...")
    
    try:
        # En mode GUI, run() bloque jusqu'à fermeture de la fenêtre
        client.run()  
    except KeyboardInterrupt:
        print("Client interrompu")

def example_2_headless_mode():
    """Exemple 2: Mode headless"""
    print("\n🤖 Exemple 2: Mode headless")
    
    client = MinecraftClient(
        position=(100, 60, 100),
        block_type="BRICK",
        enable_gui=False  # Mode headless
    )
    
    print("  🔄 Client en cours d'exécution en mode headless...")
    print("  ⏳ Appuyez sur Ctrl+C pour arrêter")
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("  Client interrompu")

def example_3_custom_position():
    """Exemple 3: Position personnalisée"""
    print("\n🎯 Exemple 3: Position et bloc personnalisés")
    
    client = MinecraftClient(
        position=(300, 70, 300),
        block_type="GRASS",
        enable_gui=True
    )
    
    print("  🎮 Client avec position personnalisée")
    print("  📝 Fermez la fenêtre quand vous avez terminé")
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("  Client interrompu")

def main():
    print("🔧 Exemples d'utilisation du Client Minecraft Abstrait")
    print("=" * 60)
    
    print("Choix disponibles:")
    print("1 - Client avec interface graphique")
    print("2 - Mode headless")  
    print("3 - Position personnalisée")
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
                example_2_headless_mode()
            elif choice == "3":
                example_3_custom_position()
            else:
                print("❌ Choix invalide, utilisez 0-3")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()