#!/usr/bin/env python3
"""
Lanceur Minecraft - Choix entre version client-serveur et autonome
================================================================

Ce script permet de choisir facilement entre :
- Version client-serveur (multijoueur)
- Version autonome (solo)

Usage:
    python3 launcher_minecraft.py
"""

import sys
import os
import subprocess
import argparse

def print_banner():
    """Affiche la bannière du lanceur."""
    print("=" * 60)
    print("🎮 MINECRAFT CLIENT - LANCEUR")
    print("=" * 60)
    print()

def print_options():
    """Affiche les options disponibles."""
    print("Choisissez votre version :")
    print()
    print("1. 🌐 Client-Serveur (Multijoueur)")
    print("   - Nécessite un serveur")
    print("   - Support multijoueur")
    print("   - Physique serveur")
    print()
    print("2. 🏠 Autonome - Interface graphique") 
    print("   - Aucun serveur requis")
    print("   - Jeu solo uniquement")
    print("   - Physique locale")
    print("   - Interface 3D complète")
    print()
    print("3. 💻 Autonome - Mode texte")
    print("   - Aucun serveur requis")
    print("   - Interface en ligne de commande")
    print("   - Idéal pour tests et serveurs")
    print()
    print("4. ℹ️  Aide et informations")
    print()
    print("0. ❌ Quitter")
    print()

def launch_client_server():
    """Lance la version client-serveur."""
    print("🌐 Lancement de la version client-serveur...")
    print()
    print("Note: Assurez-vous qu'un serveur est démarré :")
    print("  python3 server.py")
    print()
    
    try:
        subprocess.run([sys.executable, "minecraft_client_fr.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement: {e}")
        input("Appuyez sur Entrée pour continuer...")
    except FileNotFoundError:
        print("❌ Fichier minecraft_client_fr.py non trouvé")
        input("Appuyez sur Entrée pour continuer...")

def launch_standalone_gui():
    """Lance la version autonome avec interface graphique."""
    print("🏠 Lancement de la version autonome (interface graphique)...")
    
    try:
        subprocess.run([sys.executable, "minecraft_client_standalone.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement: {e}")
        print("Tentative en mode autonome simplifié...")
        launch_standalone_text()
    except FileNotFoundError:
        print("❌ Fichier minecraft_client_standalone.py non trouvé")
        print("Tentative en mode autonome simplifié...")
        launch_standalone_text()

def launch_standalone_text():
    """Lance la version autonome en mode texte."""
    print("💻 Lancement de la version autonome (mode texte)...")
    
    try:
        subprocess.run([sys.executable, "minecraft_standalone.py", "--text-mode"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement: {e}")
        input("Appuyez sur Entrée pour continuer...")
    except FileNotFoundError:
        print("❌ Fichier minecraft_standalone.py non trouvé")
        input("Appuyez sur Entrée pour continuer...")

def show_help():
    """Affiche l'aide détaillée."""
    print("ℹ️  AIDE ET INFORMATIONS")
    print("=" * 40)
    print()
    
    print("📋 VERSIONS DISPONIBLES :")
    print()
    
    print("🌐 VERSION CLIENT-SERVEUR")
    print("  Fichiers: server.py + minecraft_client_fr.py")
    print("  Démarrage:")
    print("    1. python3 server.py")
    print("    2. python3 minecraft_client_fr.py")
    print("  Avantages: Multijoueur, synchronisation")
    print("  Inconvénients: Complexité, latence")
    print()
    
    print("🏠 VERSION AUTONOME")
    print("  Fichiers: minecraft_client_standalone.py OU minecraft_standalone.py")
    print("  Démarrage:")
    print("    python3 minecraft_client_standalone.py  # Interface graphique")
    print("    python3 minecraft_standalone.py --text-mode  # Mode texte")
    print("  Avantages: Simplicité, aucune latence, hors ligne")
    print("  Inconvénients: Pas de multijoueur")
    print()
    
    print("🎮 CONTRÔLES (versions graphiques) :")
    print("  Z/Q/S/D - Mouvement (AZERTY)")
    print("  W/A/S/D - Mouvement (QWERTY)")
    print("  Espace - Saut")
    print("  Tab - Vol")
    print("  Souris - Regard")
    print("  Clic gauche - Détruire")
    print("  Clic droit - Placer")
    print("  F3 - Debug")
    print("  F5 - Sauvegarder (autonome)")
    print("  F9 - Charger (autonome)")
    print()
    
    print("💻 COMMANDES (mode texte) :")
    print("  help - Aide")
    print("  status - État du joueur")
    print("  move <x> <y> <z> - Déplacer")
    print("  fly - Vol on/off")
    print("  place <type> - Placer bloc")
    print("  break - Détruire bloc")
    print("  save <file> - Sauvegarder")
    print("  load <file> - Charger")
    print("  quit - Quitter")
    print()
    
    print("📦 TYPES DE BLOCS :")
    print("  grass, stone, wood, sand, brick, leaf")
    print()
    
    input("Appuyez sur Entrée pour continuer...")

def check_files():
    """Vérifie la présence des fichiers nécessaires."""
    files_status = {}
    
    # Fichiers requis
    required_files = [
        "minecraft_client_fr.py",
        "minecraft_client_standalone.py", 
        "minecraft_standalone.py",
        "server.py",
        "client_config.py",
        "protocol.py",
        "minecraft_physics.py",
        "noise_gen.py"
    ]
    
    for file in required_files:
        files_status[file] = os.path.exists(file)
    
    return files_status

def main():
    """Fonction principale du lanceur."""
    print_banner()
    
    # Vérifie les fichiers
    files_status = check_files()
    missing_files = [f for f, exists in files_status.items() if not exists]
    
    if missing_files:
        print("⚠️  ATTENTION: Fichiers manquants détectés:")
        for file in missing_files:
            print(f"   ❌ {file}")
        print()
        print("Certaines fonctionnalités peuvent ne pas fonctionner.")
        print()
    
    while True:
        print_options()
        
        try:
            choice = input("Votre choix (0-4) : ").strip()
            print()
            
            if choice == "1":
                if not files_status.get("minecraft_client_fr.py") or not files_status.get("server.py"):
                    print("❌ Fichiers client-serveur manquants")
                    input("Appuyez sur Entrée pour continuer...")
                    continue
                launch_client_server()
                
            elif choice == "2":
                if not files_status.get("minecraft_client_standalone.py"):
                    print("❌ minecraft_client_standalone.py manquant, basculement en mode texte")
                    launch_standalone_text()
                else:
                    launch_standalone_gui()
                    
            elif choice == "3":
                if not files_status.get("minecraft_standalone.py"):
                    print("❌ minecraft_standalone.py manquant")
                    input("Appuyez sur Entrée pour continuer...")
                    continue
                launch_standalone_text()
                
            elif choice == "4":
                show_help()
                
            elif choice == "0":
                print("👋 Au revoir!")
                break
                
            else:
                print("❌ Choix invalide, veuillez entrer un nombre entre 0 et 4")
                input("Appuyez sur Entrée pour continuer...")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except EOFError:
            break

if __name__ == "__main__":
    # Parse arguments pour mode direct
    parser = argparse.ArgumentParser(description="Lanceur Minecraft")
    parser.add_argument('--client-server', action='store_true', help='Lance directement la version client-serveur')
    parser.add_argument('--standalone-gui', action='store_true', help='Lance directement la version autonome GUI')
    parser.add_argument('--standalone-text', action='store_true', help='Lance directement la version autonome texte')
    
    args = parser.parse_args()
    
    if args.client_server:
        launch_client_server()
    elif args.standalone_gui:
        launch_standalone_gui()
    elif args.standalone_text:
        launch_standalone_text()
    else:
        main()