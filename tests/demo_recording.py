#!/usr/bin/env python3
"""
Démonstration du système d'enregistrement de gameplay
======================================================

Ce script montre comment utiliser programmatiquement le GameRecorder
pour automatiser l'enregistrement de sessions de jeu.

Usage:
    python3 demo_recording.py
"""

import sys
import os
import time

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def demonstrate_recorder_api():
    """Démontre l'utilisation de l'API GameRecorder."""
    print("=" * 60)
    print("Démonstration de l'API GameRecorder")
    print("=" * 60)
    
    from minecraft_client_fr import GameRecorder
    
    # Créer un recorder avec un répertoire personnalisé
    print("\n1. Création d'un GameRecorder...")
    recorder = GameRecorder(output_dir="demo_recordings")
    print(f"   ✅ Recorder créé - Répertoire: {recorder.output_dir}")
    
    # Configurer le FPS
    print("\n2. Configuration du FPS d'enregistrement...")
    recorder.set_fps(60)
    print(f"   ✅ FPS configuré à 60")
    
    # Démarrer l'enregistrement
    print("\n3. Démarrage de l'enregistrement...")
    session_dir = recorder.start_recording()
    print(f"   ✅ Enregistrement démarré")
    print(f"   📁 Session: {session_dir.name}")
    
    # Simuler une session de jeu
    print("\n4. Simulation d'une session de jeu (5 secondes)...")
    for i in range(5):
        time.sleep(1)
        print(f"   ⏱️  {i+1}s - Frames capturées: {recorder.frame_count}")
    
    # Arrêter l'enregistrement
    print("\n5. Arrêt de l'enregistrement...")
    recorder.stop_recording()
    
    print("\n" + "=" * 60)
    print("Démonstration terminée!")
    print("=" * 60)
    
    # Afficher le contenu du répertoire de session
    if session_dir.exists():
        files = list(session_dir.glob("*"))
        print(f"\n📂 Fichiers créés dans {session_dir}:")
        for f in files:
            print(f"   - {f.name}")


def demonstrate_multiple_sessions():
    """Démontre l'enregistrement de plusieurs sessions."""
    print("\n" + "=" * 60)
    print("Démonstration de sessions multiples")
    print("=" * 60)
    
    from minecraft_client_fr import GameRecorder
    
    recorder = GameRecorder(output_dir="demo_recordings")
    
    for i in range(3):
        print(f"\n📹 Session {i+1}/3")
        session_dir = recorder.start_recording()
        print(f"   Démarré: {session_dir.name}")
        
        # Simuler une courte session
        time.sleep(1)
        
        recorder.stop_recording()
        print(f"   Terminé avec {recorder.frame_count} frames")
        
        # Petite pause entre les sessions
        if i < 2:
            time.sleep(0.5)


def demonstrate_fps_comparison():
    """Démontre l'impact du FPS sur la capture."""
    print("\n" + "=" * 60)
    print("Comparaison de différents FPS")
    print("=" * 60)
    
    from minecraft_client_fr import GameRecorder
    
    for fps in [15, 30, 60]:
        print(f"\n🎬 Test avec {fps} FPS")
        
        recorder = GameRecorder(output_dir="demo_recordings")
        recorder.set_fps(fps)
        
        recorder.start_recording()
        time.sleep(2)  # 2 secondes d'enregistrement
        recorder.stop_recording()
        
        expected_frames = fps * 2
        print(f"   Frames attendues: ~{expected_frames}")
        print(f"   Frames capturées: {recorder.frame_count}")
        print(f"   Intervalle: {recorder.capture_interval:.4f}s")


def show_usage_examples():
    """Affiche des exemples d'utilisation."""
    print("\n" + "=" * 60)
    print("Exemples d'utilisation dans le code")
    print("=" * 60)
    
    examples = """
# Exemple 1: Enregistrement basique
from minecraft_client_fr import GameRecorder

recorder = GameRecorder()
recorder.start_recording()
# ... jouer au jeu ...
recorder.stop_recording()

# Exemple 2: Configuration personnalisée
recorder = GameRecorder(output_dir="mes_videos")
recorder.set_fps(60)  # 60 FPS pour plus de fluidité
session = recorder.start_recording()
# ... jouer au jeu ...
recorder.stop_recording()

# Exemple 3: Intégration dans une boucle de jeu
recorder = GameRecorder()
recording_active = False

def on_f9_pressed():
    global recording_active
    if not recording_active:
        recorder.start_recording()
        recording_active = True
    else:
        recorder.stop_recording()
        recording_active = False

def game_loop():
    while running:
        render_frame()
        if recording_active:
            recorder.capture_frame(window)
        
# Exemple 4: Enregistrement automatique avec timer
import threading

recorder = GameRecorder()
recorder.start_recording()

def stop_after_delay(seconds):
    time.sleep(seconds)
    recorder.stop_recording()
    print(f"Enregistrement auto-arrêté après {seconds}s")

# Arrêter après 30 secondes
timer = threading.Timer(30, stop_after_delay, args=[30])
timer.start()
"""
    
    print(examples)


def main():
    """Point d'entrée principal."""
    print("\n🎮 Démonstration du système d'enregistrement de gameplay")
    print("=========================================================\n")
    
    try:
        # Démonstration de l'API
        demonstrate_recorder_api()
        
        # Sessions multiples
        input("\n[Appuyez sur Entrée pour continuer avec les sessions multiples...]")
        demonstrate_multiple_sessions()
        
        # Comparaison FPS
        input("\n[Appuyez sur Entrée pour continuer avec la comparaison FPS...]")
        demonstrate_fps_comparison()
        
        # Exemples de code
        input("\n[Appuyez sur Entrée pour voir les exemples d'utilisation...]")
        show_usage_examples()
        
        print("\n" + "=" * 60)
        print("✅ Démonstration complète!")
        print("=" * 60)
        
        # Nettoyage
        import shutil
        demo_dir = "demo_recordings"
        if os.path.exists(demo_dir):
            print(f"\n🧹 Nettoyage du répertoire de démonstration: {demo_dir}")
            response = input("   Voulez-vous supprimer les fichiers de démonstration? [o/N] ")
            if response.lower() == 'o':
                shutil.rmtree(demo_dir)
                print(f"   ✅ {demo_dir} supprimé")
            else:
                print(f"   💾 {demo_dir} conservé")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Démonstration interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
