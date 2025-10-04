#!/usr/bin/env python3
"""
Test pour vérifier les améliorations de threading du GameRecorder
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_thread_creation():
    """Test que le thread d'écriture est créé au démarrage."""
    print("Test 1: Création du thread d'écriture")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        # Vérifier que le thread n'existe pas avant le démarrage
        assert recorder.writer_thread is None, "Thread ne devrait pas exister avant démarrage"
        assert recorder.writer_running == False, "writer_running devrait être False"
        
        # Démarrer l'enregistrement
        recorder.start_recording()
        
        # Vérifier que le thread est créé
        assert recorder.writer_thread is not None, "Thread devrait être créé"
        assert recorder.writer_running == True, "writer_running devrait être True"
        assert recorder.writer_thread.is_alive(), "Thread devrait être actif"
        
        # Arrêter l'enregistrement
        recorder.stop_recording()
        
        # Vérifier que le thread s'est arrêté
        assert recorder.writer_running == False, "writer_running devrait être False après stop"
        
        print("✅ Création du thread OK")


def test_queue_management():
    """Test que la queue est gérée correctement."""
    print("\nTest 2: Gestion de la queue")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        # Vérifier que la queue est vide au départ
        assert len(recorder.frame_queue) == 0, "Queue devrait être vide"
        
        # Démarrer l'enregistrement
        recorder.start_recording()
        
        # Simuler l'ajout de frames dans la queue
        # (nous ne pouvons pas vraiment capturer sans Pyglet, donc on simule)
        test_data = b'\x00' * (800 * 600 * 4)  # Données factices RGBA
        recorder.frame_queue.append((0, test_data, 800, 600))
        recorder.frame_queue.append((1, test_data, 800, 600))
        
        assert len(recorder.frame_queue) == 2, "Queue devrait contenir 2 frames"
        
        # Attendre un peu pour que le thread traite les frames
        time.sleep(0.5)
        
        # Arrêter l'enregistrement
        recorder.stop_recording()
        
        # Vérifier que la queue a été vidée
        assert len(recorder.frame_queue) == 0, "Queue devrait être vide après stop"
        
        print("✅ Gestion de la queue OK")


def test_stop_method_alias():
    """Test que la méthode stop() fonctionne comme alias de stop_recording()."""
    print("\nTest 3: Méthode stop() comme alias")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        # Démarrer l'enregistrement
        recorder.start_recording()
        assert recorder.is_recording == True, "Devrait être en enregistrement"
        
        # Utiliser stop() au lieu de stop_recording()
        recorder.stop()
        assert recorder.is_recording == False, "Ne devrait plus enregistrer"
        
        print("✅ Méthode stop() OK")


def test_jpeg_output_format():
    """Test que les frames sont enregistrées en JPEG."""
    print("\nTest 4: Format de sortie JPEG")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        import PIL.Image
        
        recorder = GameRecorder(output_dir=tmpdir)
        session_dir = recorder.start_recording()
        
        # Créer une image test
        test_image = PIL.Image.new('RGB', (100, 100), color='red')
        test_data = test_image.tobytes()
        
        # Ajouter à la queue (simuler une capture)
        recorder.frame_queue.append((0, test_data + b'\xff' * (100 * 100), 100, 100))
        recorder.frame_count = 1
        
        # Attendre que le thread écrive
        time.sleep(0.5)
        
        # Arrêter l'enregistrement
        recorder.stop_recording()
        
        # Vérifier que le fichier JPEG existe
        expected_file = session_dir / "frame_000000.jpg"
        assert expected_file.exists(), f"Le fichier JPEG devrait exister: {expected_file}"
        
        # Vérifier que c'est bien un JPEG
        with PIL.Image.open(expected_file) as img:
            assert img.format == 'JPEG', "Le fichier devrait être au format JPEG"
        
        print("✅ Format JPEG OK")


def test_backward_compatibility():
    """Test que l'API reste compatible avec l'ancienne version."""
    print("\nTest 5: Compatibilité API")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from minecraft_client_fr import GameRecorder
        
        recorder = GameRecorder(output_dir=tmpdir)
        
        # Vérifier que toutes les méthodes publiques existent
        assert hasattr(recorder, 'start_recording'), "Méthode start_recording manquante"
        assert hasattr(recorder, 'stop_recording'), "Méthode stop_recording manquante"
        assert hasattr(recorder, 'stop'), "Méthode stop manquante"
        assert hasattr(recorder, 'capture_frame'), "Méthode capture_frame manquante"
        assert hasattr(recorder, 'set_fps'), "Méthode set_fps manquante"
        
        # Vérifier que les attributs publics existent
        assert hasattr(recorder, 'output_dir'), "Attribut output_dir manquant"
        assert hasattr(recorder, 'is_recording'), "Attribut is_recording manquant"
        assert hasattr(recorder, 'frame_count'), "Attribut frame_count manquant"
        assert hasattr(recorder, 'session_dir'), "Attribut session_dir manquant"
        
        print("✅ Compatibilité API OK")


def main():
    """Point d'entrée des tests."""
    print("=" * 60)
    print("Tests des améliorations threading du GameRecorder")
    print("=" * 60)
    
    try:
        test_thread_creation()
        test_queue_management()
        test_stop_method_alias()
        test_jpeg_output_format()
        test_backward_compatibility()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests ont réussi!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Échec du test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
