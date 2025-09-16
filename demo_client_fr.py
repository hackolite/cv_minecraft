#!/usr/bin/env python3
"""
Démonstration du Client Minecraft Français
==========================================

Ce script montre comment utiliser le nouveau client amélioré.
"""

import os
import subprocess
import sys
import time

def print_banner():
    """Affiche la bannière du client."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                🎮 CLIENT MINECRAFT FRANÇAIS 🇫🇷                ║
║                                                              ║
║  Un client Minecraft amélioré avec Pyglet et support        ║
║  français complet pour le serveur cv_minecraft              ║
╚══════════════════════════════════════════════════════════════╝
""")

def show_features():
    """Affiche les fonctionnalités du client."""
    print("🚀 FONCTIONNALITÉS PRINCIPALES:")
    print("  ✅ Interface 100% française")
    print("  ✅ Support clavier AZERTY natif")
    print("  ✅ Configuration flexible (JSON)")
    print("  ✅ Reconnexion automatique")
    print("  ✅ Gestion d'erreurs avancée")
    print("  ✅ Compatible serveur existant")
    print("  ✅ Arguments ligne de commande")
    print()

def show_usage_examples():
    """Affiche des exemples d'utilisation."""
    print("📚 EXEMPLES D'UTILISATION:")
    print()
    
    print("1. 🏠 Lancement basique (serveur local):")
    print("   python3 minecraft_client_fr.py")
    print()
    
    print("2. 🌐 Connexion serveur distant:")
    print("   python3 minecraft_client_fr.py --server 192.168.1.100:8765")
    print()
    
    print("3. 🖥️  Mode plein écran avec debug:")
    print("   python3 minecraft_client_fr.py --fullscreen --debug")
    print()
    
    print("4. ⚙️  Configuration personnalisée:")
    print("   python3 minecraft_client_fr.py --config config_exemple_qwerty.json")
    print()
    
    print("5. 🗣️  Interface en anglais:")
    print("   python3 minecraft_client_fr.py --lang en")
    print()
    
    print("6. 🔧 Aide et diagnostics:")
    print("   python3 launcher.py --help")
    print("   python3 launcher.py --check")
    print()

def show_controls():
    """Affiche les contrôles du jeu."""
    print("🎮 CONTRÔLES (Layout AZERTY):")
    print("  🏃 Mouvement:")
    print("    Z - Avancer")
    print("    S - Reculer") 
    print("    Q - Aller à gauche")
    print("    D - Aller à droite")
    print()
    
    print("  🦘 Actions:")
    print("    Espace - Saut")
    print("    Maj - S'accroupir")
    print("    R - Courir")
    print("    Tab - Vol on/off")
    print()
    
    print("  🔧 Interface:")
    print("    F3 - Debug on/off")
    print("    F11 - Plein écran")
    print("    Échap - Libérer souris")
    print("    1-5 - Sélection bloc")
    print()
    
    print("  🖱️  Souris:")
    print("    Clic gauche - Détruire bloc")
    print("    Clic droit - Placer bloc")
    print("    Mouvement - Regarder")
    print()

def check_server_status():
    """Vérifie si le serveur est en cours d'exécution."""
    print("🔍 Vérification du statut du serveur...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_client_francais.py"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Serveur disponible et compatible")
            return True
        else:
            print("❌ Serveur non disponible ou problème de compatibilité")
            print("💡 Démarrez le serveur avec: python3 server.py")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout lors de la vérification du serveur")
        return False
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification: {e}")
        return False

def interactive_demo():
    """Démonstration interactive."""
    print("🎯 DÉMONSTRATION INTERACTIVE:")
    print()
    
    while True:
        print("Choisissez une option:")
        print("  1. 🚀 Lancer le client (serveur local)")
        print("  2. 🔧 Tester l'environnement")
        print("  3. 📋 Afficher l'aide complète")
        print("  4. 🌐 Tester la connexion serveur")
        print("  5. ⚙️  Créer configuration personnalisée")
        print("  6. 🚪 Quitter")
        print()
        
        try:
            choice = input("Votre choix (1-6): ").strip()
            print()
            
            if choice == "1":
                print("🚀 Lancement du client...")
                print("💡 Fermez la fenêtre ou appuyez Ctrl+C pour revenir ici")
                print()
                
                try:
                    subprocess.run([sys.executable, "minecraft_client_fr.py"])
                except KeyboardInterrupt:
                    print("\n🔙 Retour au menu")
                except Exception as e:
                    print(f"❌ Erreur: {e}")
                    
            elif choice == "2":
                print("🔧 Test de l'environnement...")
                subprocess.run([sys.executable, "launcher.py", "--check"])
                
            elif choice == "3":
                subprocess.run([sys.executable, "launcher.py", "--help"])
                
            elif choice == "4":
                check_server_status()
                
            elif choice == "5":
                create_custom_config()
                
            elif choice == "6":
                print("👋 Au revoir!")
                break
                
            else:
                print("❌ Choix invalide. Utilisez 1-6.")
                
            print("\n" + "="*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except EOFError:
            print("\n\n👋 Au revoir!")
            break

def create_custom_config():
    """Assistant de création de configuration."""
    print("⚙️  ASSISTANT DE CONFIGURATION")
    print("Créons une configuration personnalisée pour vous!")
    print()
    
    try:
        # Configuration serveur
        print("🌐 Configuration serveur:")
        host = input("Adresse serveur (défaut: localhost): ").strip() or "localhost"
        port_str = input("Port serveur (défaut: 8765): ").strip() or "8765"
        port = int(port_str)
        
        # Configuration graphique
        print("\n🖥️  Configuration graphique:")
        width_str = input("Largeur fenêtre (défaut: 1280): ").strip() or "1280"
        height_str = input("Hauteur fenêtre (défaut: 720): ").strip() or "720"
        width = int(width_str)
        height = int(height_str)
        
        fullscreen = input("Plein écran? (o/N): ").strip().lower() == 'o'
        
        # Configuration clavier
        print("\n⌨️  Configuration clavier:")
        layout = input("Layout clavier (azerty/qwerty, défaut: azerty): ").strip().lower() or "azerty"
        
        # Configuration joueur
        print("\n👤 Configuration joueur:")
        name = input("Nom du joueur (défaut: Joueur): ").strip() or "Joueur"
        
        # Création de la configuration
        config = {
            "server": {
                "host": host,
                "port": port,
                "auto_reconnect": True,
                "connection_timeout": 10
            },
            "graphics": {
                "window_width": width,
                "window_height": height,
                "fullscreen": fullscreen,
                "vsync": True,
                "fov": 70.0,
                "render_distance": 60.0
            },
            "controls": {
                "keyboard_layout": layout,
                "mouse_sensitivity": 0.15,
                "invert_mouse_y": False
            },
            "interface": {
                "language": "fr",
                "show_debug_info": True,
                "crosshair_color": [255, 255, 255]
            },
            "player": {
                "name": name,
                "movement_speed": 5.0,
                "jump_speed": 8.0,
                "flying_speed": 15.0
            }
        }
        
        # Sauvegarde
        import json
        filename = f"config_personnalisee_{name.lower()}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Configuration sauvée: {filename}")
        print(f"🚀 Utilisez-la avec: python3 minecraft_client_fr.py --config {filename}")
        
    except (ValueError, KeyboardInterrupt):
        print("\n❌ Configuration annulée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

def main():
    """Fonction principale de démonstration."""
    print_banner()
    show_features()
    show_usage_examples()
    show_controls()
    
    print("🤔 Que souhaitez-vous faire?")
    print("  I - 🎮 Démonstration interactive")
    print("  Q - 🚪 Quitter")
    print()
    
    try:
        choice = input("Votre choix (I/Q): ").strip().upper()
        print()
        
        if choice == "I":
            interactive_demo()
        elif choice == "Q":
            print("👋 Au revoir!")
        else:
            print("❌ Choix invalide")
            
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Au revoir!")

if __name__ == "__main__":
    main()