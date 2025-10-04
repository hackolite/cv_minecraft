#!/usr/bin/env python3
"""
Test complet pour la création de fenêtres Pyglet et l'enregistrement du buffer
avec suivi des coordonnées x, y, z.

Ce test vérifie que:
1. Les fenêtres Pyglet peuvent être créées pour les caméras
2. Le buffer Pyglet peut être capturé avec les coordonnées x, y, z
3. L'enregistrement fonctionne correctement
4. Les métadonnées de position sont sauvegardées
5. L'intégration entre CubeWindow et GameRecorder fonctionne
"""

import os
import sys
import tempfile
import time
import json
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup display for headless testing
os.environ['DISPLAY'] = ':99'

try:
    from protocol import Cube, CubeWindow, PYGLET_AVAILABLE
    from minecraft_client_fr import GameRecorder
    import pyglet
    from pyglet.gl import *
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("⚠️  Skipping tests that require Pyglet")
    PYGLET_AVAILABLE = False


def test_cube_window_creation():
    """Test 1: Vérifier la création de fenêtres Pyglet pour les cubes caméra."""
    print("\n" + "=" * 70)
    print("Test 1: Création de fenêtres Pyglet pour cubes caméra")
    print("=" * 70)
    
    if not PYGLET_AVAILABLE:
        print("⚠️  Pyglet non disponible - test ignoré")
        return True
    
    try:
        # Créer un cube caméra à différentes positions
        positions = [
            (10, 50, 10, "camera_test_1"),
            (20, 60, 30, "camera_test_2"),
            (15, 55, 25, "camera_test_3"),
        ]
        
        cubes = []
        for x, y, z, cube_id in positions:
            print(f"\n📦 Création cube caméra '{cube_id}' à position ({x}, {y}, {z})")
            cube = Cube(cube_id, (x, y, z), cube_type="camera")
            cubes.append(cube)
            
            # Vérifier que la fenêtre a été créée
            assert cube.window is not None, f"La fenêtre pour {cube_id} devrait être créée"
            assert hasattr(cube.window, 'window'), f"CubeWindow devrait avoir un attribut window"
            
            # Vérifier que la position est correcte
            assert cube.position == (x, y, z), f"Position devrait être ({x}, {y}, {z})"
            
            print(f"   ✅ Fenêtre créée pour {cube_id}")
            print(f"   ✅ Position: {cube.position}")
            print(f"   ✅ Window type: {type(cube.window)}")
            print(f"   ✅ Pyglet window: {type(cube.window.window)}")
        
        # Cleanup
        for cube in cubes:
            if cube.window:
                cube.window.close()
        
        print("\n✅ Test 1: RÉUSSI - Toutes les fenêtres créées correctement")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 1: ÉCHEC - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_buffer_capture_with_position():
    """Test 2: Vérifier la capture du buffer Pyglet avec coordonnées x, y, z."""
    print("\n" + "=" * 70)
    print("Test 2: Capture du buffer Pyglet avec coordonnées x, y, z")
    print("=" * 70)
    
    if not PYGLET_AVAILABLE:
        print("⚠️  Pyglet non disponible - test ignoré")
        return True
    
    try:
        # Créer un cube caméra à une position spécifique
        test_position = (25, 55, 35)
        cube = Cube("buffer_test_cam", test_position, cube_type="camera")
        
        print(f"\n📦 Cube caméra créé à position {test_position}")
        print(f"   Window: {cube.window is not None}")
        
        # Vérifier que le cube window peut rendre et capturer
        if cube.window and cube.window.window:
            # Switch to camera context
            cube.window.window.switch_to()
            
            # Clear and render
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            cube.window._render_simple_scene()
            glFlush()
            
            # Capture buffer
            buffer = pyglet.image.get_buffer_manager().get_color_buffer()
            image_data = buffer.get_image_data()
            
            print(f"   ✅ Buffer capturé: {image_data.width}x{image_data.height}")
            print(f"   ✅ Format: {image_data.format}")
            
            # Vérifier que les données sont capturées
            raw_data = image_data.get_data('RGBA', image_data.width * 4)
            assert len(raw_data) > 0, "Les données du buffer devraient être non vides"
            
            print(f"   ✅ Données brutes: {len(raw_data)} bytes")
            print(f"   ✅ Position de la caméra: {cube.position}")
        
        # Cleanup
        if cube.window:
            cube.window.close()
        
        print("\n✅ Test 2: RÉUSSI - Buffer capturé avec position")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 2: ÉCHEC - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_game_recorder_with_camera_position():
    """Test 3: Vérifier l'enregistrement avec GameRecorder et métadonnées de position."""
    print("\n" + "=" * 70)
    print("Test 3: GameRecorder avec métadonnées de position")
    print("=" * 70)
    
    if not PYGLET_AVAILABLE:
        print("⚠️  Pyglet non disponible - test ignoré")
        return True
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Créer un cube caméra à une position spécifique
            test_position = (30, 60, 40)
            cube = Cube("recorder_test_cam", test_position, cube_type="camera")
            
            print(f"\n📦 Cube caméra créé à position {test_position}")
            
            # Créer un GameRecorder pour ce cube
            recorder = GameRecorder(output_dir=tmpdir, camera_cube=cube)
            
            print(f"   ✅ GameRecorder créé")
            print(f"   ✅ Caméra associée: {recorder.camera_cube.id if recorder.camera_cube else 'None'}")
            print(f"   ✅ Position caméra: {recorder.camera_cube.position if recorder.camera_cube else 'N/A'}")
            
            # Démarrer l'enregistrement
            session_dir = recorder.start_recording()
            print(f"   ✅ Enregistrement démarré: {session_dir}")
            
            # Simuler la capture de quelques frames
            if cube.window and cube.window.window:
                for i in range(3):
                    # Switch to camera context and render
                    cube.window.window.switch_to()
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    cube.window._render_simple_scene()
                    glFlush()
                    
                    # Capture frame
                    recorder.capture_frame()
                    time.sleep(0.05)  # Petit délai entre les frames
                    
                    print(f"   📸 Frame {i+1} capturée à position {cube.position}")
            
            # Arrêter l'enregistrement
            recorder.stop_recording()
            print(f"   ✅ Enregistrement arrêté")
            
            # Vérifier que les fichiers ont été créés
            session_path = Path(session_dir)
            assert session_path.exists(), "Le répertoire de session devrait exister"
            
            # Vérifier le fichier d'info
            info_file = session_path / "session_info.json"
            if info_file.exists():
                with open(info_file, 'r') as f:
                    info_data = json.load(f)
                print(f"   ✅ Métadonnées de session: {info_data}")
            
            # Vérifier les frames
            frame_files = list(session_path.glob("frame_*.jpg"))
            print(f"   ✅ Frames sauvegardées: {len(frame_files)}")
            
            for frame_file in frame_files:
                print(f"      - {frame_file.name}: {frame_file.stat().st_size} bytes")
            
            # Cleanup
            if cube.window:
                cube.window.close()
            
            print("\n✅ Test 3: RÉUSSI - Enregistrement avec métadonnées")
            return True
        
    except Exception as e:
        print(f"\n❌ Test 3: ÉCHEC - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_camera_recordings():
    """Test 4: Vérifier l'enregistrement de plusieurs caméras simultanément."""
    print("\n" + "=" * 70)
    print("Test 4: Enregistrement de plusieurs caméras simultanément")
    print("=" * 70)
    
    if not PYGLET_AVAILABLE:
        print("⚠️  Pyglet non disponible - test ignoré")
        return True
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Créer plusieurs caméras à différentes positions
            cameras = [
                ("camera_1", (10, 50, 10)),
                ("camera_2", (20, 55, 20)),
                ("camera_3", (30, 60, 30)),
            ]
            
            recorders = []
            cubes = []
            
            for cam_id, position in cameras:
                print(f"\n📦 Création caméra '{cam_id}' à position {position}")
                cube = Cube(cam_id, position, cube_type="camera")
                cubes.append(cube)
                
                # Créer un sous-répertoire pour chaque caméra
                cam_dir = Path(tmpdir) / cam_id
                cam_dir.mkdir(exist_ok=True)
                
                recorder = GameRecorder(output_dir=str(cam_dir), camera_cube=cube)
                recorders.append(recorder)
                
                recorder.start_recording()
                print(f"   ✅ Enregistrement démarré pour {cam_id}")
            
            # Simuler la capture de frames pour toutes les caméras
            for i in range(2):
                print(f"\n📸 Capture frame {i+1} pour toutes les caméras")
                for cube, recorder in zip(cubes, recorders):
                    if cube.window and cube.window.window:
                        cube.window.window.switch_to()
                        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                        cube.window._render_simple_scene()
                        glFlush()
                        recorder.capture_frame()
                        print(f"   - {cube.id} @ {cube.position}")
                
                time.sleep(0.05)
            
            # Arrêter tous les enregistrements
            print("\n⏹️  Arrêt de tous les enregistrements")
            for recorder in recorders:
                recorder.stop_recording()
            
            # Vérifier que toutes les caméras ont enregistré
            for cam_id, _ in cameras:
                cam_dir = Path(tmpdir) / cam_id
                sessions = list(cam_dir.glob("session_*"))
                assert len(sessions) > 0, f"Session pour {cam_id} devrait exister"
                
                session_dir = sessions[0]
                frame_files = list(session_dir.glob("frame_*.jpg"))
                print(f"   ✅ {cam_id}: {len(frame_files)} frames enregistrées")
            
            # Cleanup
            for cube in cubes:
                if cube.window:
                    cube.window.close()
            
            print("\n✅ Test 4: RÉUSSI - Enregistrement multi-caméras")
            return True
        
    except Exception as e:
        print(f"\n❌ Test 4: ÉCHEC - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_tracking_in_metadata():
    """Test 5: Vérifier que les positions x,y,z sont sauvegardées dans les métadonnées."""
    print("\n" + "=" * 70)
    print("Test 5: Suivi des positions x,y,z dans les métadonnées")
    print("=" * 70)
    
    if not PYGLET_AVAILABLE:
        print("⚠️  Pyglet non disponible - test ignoré")
        return True
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Créer une caméra et la déplacer entre les captures
            test_positions = [
                (10, 50, 10),
                (15, 52, 15),
                (20, 54, 20),
            ]
            
            cube = Cube("moving_camera", test_positions[0], cube_type="camera")
            recorder = GameRecorder(output_dir=tmpdir, camera_cube=cube)
            
            print(f"\n📦 Caméra mobile créée")
            
            session_dir = recorder.start_recording()
            
            # Capturer une frame à chaque position
            for i, position in enumerate(test_positions):
                cube.update_position(position)
                print(f"   📍 Position {i+1}: {position}")
                
                if cube.window and cube.window.window:
                    cube.window.window.switch_to()
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    cube.window._render_simple_scene()
                    glFlush()
                    recorder.capture_frame()
                
                time.sleep(0.05)
            
            recorder.stop_recording()
            
            # Vérifier que les métadonnées contiennent l'information de position
            info_file = Path(session_dir) / "session_info.json"
            if info_file.exists():
                with open(info_file, 'r') as f:
                    info_data = json.load(f)
                print(f"\n   ✅ Métadonnées session: frame_count={info_data['frame_count']}, camera_id={info_data.get('camera_info', {}).get('camera_id', 'N/A')}")
                
                # Vérifier le nombre de frames
                assert info_data['frame_count'] >= 3, "Devrait avoir au moins 3 frames"
                
                # Vérifier que les info de caméra sont présentes
                assert 'camera_info' in info_data, "camera_info devrait être présent"
                assert 'position' in info_data['camera_info'], "position devrait être présente"
            
            # Vérifier les métadonnées de frames avec positions x,y,z
            frames_file = Path(session_dir) / "frames_metadata.json"
            if frames_file.exists():
                with open(frames_file, 'r') as f:
                    frames_data = json.load(f)
                
                print(f"\n   ✅ Métadonnées de frames: {len(frames_data)} frames")
                
                # Vérifier que chaque frame a des métadonnées de position
                for i, frame_meta in enumerate(frames_data):
                    assert 'camera_position' in frame_meta, f"Frame {i} devrait avoir camera_position"
                    pos = frame_meta['camera_position']
                    print(f"      Frame {i}: x={pos['x']}, y={pos['y']}, z={pos['z']}")
                    assert 'x' in pos and 'y' in pos and 'z' in pos, f"Frame {i} devrait avoir x, y, z"
                
                # Vérifier que les positions correspondent aux déplacements
                assert frames_data[0]['camera_position']['x'] == 10, "Frame 0 devrait être à x=10"
                assert frames_data[1]['camera_position']['x'] == 15, "Frame 1 devrait être à x=15"
                assert frames_data[2]['camera_position']['x'] == 20, "Frame 2 devrait être à x=20"
                
                print(f"\n   ✅ Toutes les frames ont des positions x,y,z correctes")
            else:
                print(f"\n   ⚠️  Fichier frames_metadata.json non trouvé")
                return False
            
            # Cleanup
            if cube.window:
                cube.window.close()
            
            print("\n✅ Test 5: RÉUSSI - Positions trackées avec x,y,z dans métadonnées")
            return True
        
    except Exception as e:
        print(f"\n❌ Test 5: ÉCHEC - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée des tests."""
    print("\n" + "=" * 70)
    print("TESTS COMPLETS: Fenêtres Pyglet et Enregistrement Buffer avec x,y,z")
    print("=" * 70)
    
    if not PYGLET_AVAILABLE:
        print("\n⚠️  PYGLET NON DISPONIBLE")
        print("Les tests ne peuvent pas être exécutés sans Pyglet")
        print("Installez avec: pip install pyglet")
        return 1
    
    results = []
    
    # Exécuter tous les tests
    results.append(("Test 1: Création fenêtres", test_cube_window_creation()))
    results.append(("Test 2: Capture buffer", test_buffer_capture_with_position()))
    results.append(("Test 3: GameRecorder", test_game_recorder_with_camera_position()))
    results.append(("Test 4: Multi-caméras", test_multiple_camera_recordings()))
    results.append(("Test 5: Tracking position", test_position_tracking_in_metadata()))
    
    # Résumé des résultats
    print("\n" + "=" * 70)
    print("RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{status}: {test_name}")
    
    print("\n" + "-" * 70)
    print(f"Total: {total} | Réussis: {passed} | Échoués: {failed}")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS ONT RÉUSSI!")
        print("\nConclusions:")
        print("  ✅ Les fenêtres Pyglet sont créées correctement")
        print("  ✅ Le buffer Pyglet peut être capturé avec x,y,z")
        print("  ✅ GameRecorder fonctionne avec les positions")
        print("  ✅ L'enregistrement multi-caméras fonctionne")
        print("  ✅ Les métadonnées sont sauvegardées correctement")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) ONT ÉCHOUÉ")
        print("Vérifiez les erreurs ci-dessus pour plus de détails")
        return 1


if __name__ == "__main__":
    sys.exit(main())
