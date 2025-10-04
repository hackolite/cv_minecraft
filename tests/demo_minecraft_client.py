#!/usr/bin/env python3
"""
Démonstration du Client Minecraft Abstrait
==========================================

Ce script montre comment utiliser la nouvelle classe MinecraftClient
pour créer un client Minecraft.

Usage:
    # Mode GUI (pour jouer normalement)
    python3 demo_minecraft_client.py --gui
    
    # Mode headless
    python3 demo_minecraft_client.py --headless
    
    # Configuration personnalisée
    python3 demo_minecraft_client.py --position 100 150 100 --block-type BRICK
"""

import sys
import argparse
from minecraft_client import MinecraftClient

def main():
    parser = argparse.ArgumentParser(description="Démonstration du Client Minecraft Abstrait")
    parser.add_argument('--gui', action='store_true', help='Mode GUI (interface graphique)')
    parser.add_argument('--headless', action='store_true', help='Mode headless')
    parser.add_argument('--position', nargs=3, type=float, default=[50, 80, 50],
                       help='Position de départ [x y z]')
    parser.add_argument('--block-type', default='GRASS', 
                       help='Type de bloc par défaut (GRASS, STONE, SAND, BRICK)')
    
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
    
    # Créer le client
    client = MinecraftClient(
        position=tuple(args.position),
        block_type=args.block_type,
        enable_gui=enable_gui
    )
    
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
        print("  - Ctrl+C pour arrêter")
    
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