#!/usr/bin/env python3
"""
Test pour le système GameRecorder
"""

import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_game_recorder_init():
    """Test l'initialisation du GameRecorder."""
    print("Test 1: Initialisation du GameRecorder")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Import ici pour éviter les problèmes de display
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        assert recorder.output_dir == Path(tmpdir), "Répertoire de sortie incorrect"
        assert recorder.is_recording == False, "Ne devrait pas enregistrer au démarrage"
        assert recorder.frame_count == 0, "Compteur de frames devrait être à 0"
        
        print("✅ Initialisation OK")


def test_game_recorder_start_stop():
    """Test le démarrage et l'arrêt de l'enregistrement."""
    print("\nTest 2: Démarrage et arrêt de l'enregistrement")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        # Démarrer l'enregistrement
        session_dir = recorder.start_recording()
        
        assert recorder.is_recording == True, "Devrait être en train d'enregistrer"
        assert recorder.start_time is not None, "start_time devrait être défini"
        assert session_dir.exists(), "Le répertoire de session devrait exister"
        
        # Attendre un peu
        time.sleep(0.1)
        
        # Arrêter l'enregistrement
        recorder.stop_recording()
        
        assert recorder.is_recording == False, "Ne devrait plus enregistrer"
        
        # Vérifier que le fichier d'info existe
        info_file = session_dir / "session_info.json"
        assert info_file.exists(), "Le fichier session_info.json devrait exister"
        
        print("✅ Démarrage et arrêt OK")


def test_game_recorder_fps_setting():
    """Test le réglage du FPS."""
    print("\nTest 3: Réglage du FPS")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        # Test différents FPS
        for fps in [15, 30, 60]:
            recorder.set_fps(fps)
            expected_interval = 1.0 / fps
            assert abs(recorder.capture_interval - expected_interval) < 0.0001, \
                f"Intervalle de capture incorrect pour {fps} FPS"
        
        print("✅ Réglage FPS OK")


def test_game_recorder_multiple_sessions():
    """Test plusieurs sessions d'enregistrement."""
    print("\nTest 4: Sessions multiples")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        # Première session
        session1 = recorder.start_recording()
        time.sleep(0.1)
        recorder.stop_recording()
        
        # Deuxième session
        time.sleep(0.1)  # Attendre pour avoir un timestamp différent
        session2 = recorder.start_recording()
        time.sleep(0.1)
        recorder.stop_recording()
        
        # Vérifier que les deux sessions existent et sont différentes
        assert session1 != session2, "Les sessions devraient être différentes"
        assert session1.exists(), "La première session devrait exister"
        assert session2.exists(), "La deuxième session devrait exister"
        
        print("✅ Sessions multiples OK")


def main():
    """Point d'entrée des tests."""
    print("=" * 60)
    print("Tests du système GameRecorder")
    print("=" * 60)
    
    try:
        test_game_recorder_init()
        test_game_recorder_start_stop()
        test_game_recorder_fps_setting()
        test_game_recorder_multiple_sessions()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests ont réussi!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Échec du test: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
