#!/usr/bin/env python3
"""
Lanceur pour le Client Minecraft Français
=========================================

Ce script permet de lancer le client Minecraft avec différentes options
et gère les cas où OpenGL n'est pas disponible (environnements sans tête).
"""

import sys
import os
import argparse

def show_help():
    """Affiche l'aide du client."""
    print("""
🎮 Client Minecraft Français - Aide
===================================

USAGE:
    python3 minecraft_client_fr.py [OPTIONS]
    python3 launcher.py [OPTIONS]

OPTIONS:
    --server, -s HOST:PORT    Adresse du serveur (défaut: localhost:8765)
    --config, -c FILE         Fichier de configuration (défaut: client_config.json)
    --fullscreen, -f          Démarrer en plein écran
    --debug, -d               Activer le mode debug
    --lang LANG               Langue de l'interface (fr/en, défaut: fr)
    --help, -h                Afficher cette aide

EXEMPLES:
    # Connexion locale par défaut
    python3 minecraft_client_fr.py
    
    # Connexion à un serveur distant
    python3 minecraft_client_fr.py --server 192.168.1.100:8765
    
    # Mode plein écran avec debug
    python3 minecraft_client_fr.py --fullscreen --debug
    
    # Utilisation d'un fichier de configuration personnalisé
    python3 minecraft_client_fr.py --config mon_config.json

CONTRÔLES (Layout AZERTY par défaut):
    Z/Q/S/D       Mouvement (avant/gauche/arrière/droite)
    Espace        Saut
    Maj Gauche    S'accroupir
    R             Courir
    Tab           Activer/désactiver le vol
    F3            Afficher/masquer les informations de debug
    F11           Basculer en plein écran
    Échap         Libérer le curseur de la souris
    1-5           Sélectionner un type de bloc
    
    Clic gauche   Détruire un bloc
    Clic droit    Placer un bloc

CONFIGURATION:
    Le client génère automatiquement un fichier client_config.json
    avec toutes les options configurables :
    - Paramètres réseau (serveur, timeout, reconnexion)
    - Paramètres graphiques (résolution, FOV, distance de rendu)
    - Contrôles (layout clavier, sensibilité souris)
    - Interface (langue, couleurs, affichage debug)
    - Audio (volumes, effets)
    - Joueur (nom, vitesses, position de spawn)

COMPATIBILITÉ:
    - Pyglet 1.5.27+ pour le rendu
    - WebSockets pour la communication réseau
    - Support Windows/Mac/Linux
    - Layout clavier AZERTY et QWERTY
    - Interface en français et anglais

DÉPENDANCES:
    pip install -r requirements.txt
    
    Packages requis:
    - pyglet==1.5.27
    - websockets==12.0
    - PyOpenGL
    - asyncio

PROBLÈMES COURANTS:
    1. "Library GLU not found" → Installer les bibliothèques OpenGL système
    2. "Connection failed" → Vérifier que le serveur fonctionne
    3. "Permission denied" → Vérifier les droits d'écriture pour le config
    
Pour plus d'informations, voir README.md et CONVERSION_GUIDE.md
""")

def check_environment():
    """Vérifie l'environnement d'exécution."""
    issues = []
    
    # Vérification Python
    if sys.version_info < (3, 6):
        issues.append("Python 3.6+ requis")
    
    # Vérification des modules
    try:
        import pyglet
    except ImportError:
        issues.append("Pyglet non installé (pip install pyglet==1.5.27)")
    
    try:
        import websockets
    except ImportError:
        issues.append("WebSockets non installé (pip install websockets==12.0)")
    
    try:
        import OpenGL.GL
    except ImportError:
        issues.append("PyOpenGL non installé (pip install PyOpenGL)")
    
    # Vérification des fichiers
    required_files = ['protocol.py', 'texture.png']
    for file in required_files:
        if not os.path.exists(file):
            issues.append(f"Fichier manquant: {file}")
    
    return issues

def main():
    """Point d'entrée principal du lanceur."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('--check', action='store_true', help='Vérifier l\'environnement')
    args, remaining = parser.parse_known_args()
    
    if args.help:
        show_help()
        return 0
    
    if args.check:
        print("🔍 Vérification de l'environnement...")
        issues = check_environment()
        
        if not issues:
            print("✅ Environnement OK - prêt à lancer le client")
            return 0
        else:
            print("❌ Problèmes détectés:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
    
    # Tentative de lancement du client principal
    try:
        print("🚀 Lancement du client Minecraft...")
        
        # Reconstruction des arguments
        sys.argv = ['minecraft_client_fr.py'] + remaining
        
        # Import et lancement du client principal
        import minecraft_client_fr
        return minecraft_client_fr.main()
        
    except ImportError as e:
        if "GLU" in str(e) or "OpenGL" in str(e):
            print("❌ Erreur OpenGL: Environnement graphique non disponible")
            print("💡 Ce programme nécessite un environnement graphique avec OpenGL")
            print("💡 Sur un serveur, utilisez Xvfb ou un bureau virtuel")
            return 1
        else:
            print(f"❌ Erreur d'import: {e}")
            return 1
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())