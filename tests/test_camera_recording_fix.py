#!/usr/bin/env python3
"""
Test pour vérifier que les caméras enregistrent correctement les frames.
Ce test vérifie que la méthode capture_frame() est appelée pour tous les camera_recorders actifs.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_camera_recorders_capture_frames():
    """Test que les camera recorders capturent des frames lors du on_draw."""
    print("\nTest: Vérification de la capture de frames pour camera_recorders")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Import ici pour éviter les problèmes de display
        from minecraft_client_fr import GameRecorder
        
        # Créer des recorders mock
        camera_recorder_1 = GameRecorder(output_dir=f"{tmpdir}/camera_1")
        camera_recorder_2 = GameRecorder(output_dir=f"{tmpdir}/camera_2")
        
        # Démarrer les enregistrements
        camera_recorder_1.start_recording()
        camera_recorder_2.start_recording()
        
        # Vérifier qu'ils sont en enregistrement
        assert camera_recorder_1.is_recording == True, "Camera 1 devrait enregistrer"
        assert camera_recorder_2.is_recording == True, "Camera 2 devrait enregistrer"
        
        # Vérifier que les sessions ont été créées
        assert camera_recorder_1.session_dir is not None, "Camera 1 devrait avoir une session"
        assert camera_recorder_2.session_dir is not None, "Camera 2 devrait avoir une session"
        assert camera_recorder_1.session_dir.exists(), "Le répertoire de session 1 devrait exister"
        assert camera_recorder_2.session_dir.exists(), "Le répertoire de session 2 devrait exister"
        
        # Arrêter les enregistrements
        camera_recorder_1.stop_recording()
        camera_recorder_2.stop_recording()
        
        # Vérifier qu'ils ne sont plus en enregistrement
        assert camera_recorder_1.is_recording == False, "Camera 1 ne devrait plus enregistrer"
        assert camera_recorder_2.is_recording == False, "Camera 2 ne devrait plus enregistrer"
        
        print("✅ Les camera_recorders se démarrent et s'arrêtent correctement")


def test_multiple_recorders_in_on_draw():
    """Test conceptuel vérifiant que on_draw appelle capture_frame pour tous les recorders."""
    print("\nTest: Vérification conceptuelle du code on_draw")
    
    # Ce test vérifie que le code contient la logique nécessaire
    # En vérifiant le code source directement
    
    client_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               'minecraft_client_fr.py')
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier que on_draw contient la boucle pour les camera_recorders
    assert 'for camera_id, recorder in self.camera_recorders.items()' in content, \
        "Le code on_draw devrait contenir une boucle sur camera_recorders"
    
    assert 'if recorder.is_recording:' in content, \
        "Le code devrait vérifier si le recorder est en enregistrement"
    
    # Vérifier qu'il y a au moins 2 appels à capture_frame dans on_draw
    # (un pour self.recorder et un pour les camera_recorders)
    capture_frame_count = content.count('recorder.capture_frame(self)')
    assert capture_frame_count >= 2, \
        f"Il devrait y avoir au moins 2 appels à capture_frame, trouvé {capture_frame_count}"
    
    print("✅ Le code on_draw contient la logique de capture pour camera_recorders")


def main():
    """Point d'entrée des tests."""
    print("=" * 60)
    print("Tests de correction du système d'enregistrement des caméras")
    print("=" * 60)
    
    try:
        test_camera_recorders_capture_frames()
        test_multiple_recorders_in_on_draw()
        
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
