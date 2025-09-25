#!/usr/bin/env python3
"""
Test du système de streaming caméra RTSP
Test for RTSP camera streaming system
"""

import asyncio
import logging
import time
from observer_camera import camera_manager, ObserverCamera
from rtsp_video_streamer import EnhancedRTSPServer
from user_manager import CameraUser

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

async def test_camera_creation():
    """Test de création et capture de caméra d'observateur."""
    logging.info("🧪 Test de création de caméra d'observateur")
    
    # Créer une caméra
    camera = camera_manager.create_camera(
        observer_id="test_observer",
        position=(30.0, 50.0, 80.0),
        rotation=(0.0, 0.0),
        resolution=(640, 480)
    )
    
    assert camera is not None, "La caméra n'a pas été créée"
    assert camera.observer_id == "test_observer", "ID observateur incorrect"
    assert camera.position == (30.0, 50.0, 80.0), "Position incorrecte"
    
    # Démarrer la capture (sans modèle du monde pour le test)
    camera.start_capture(None)
    
    # Attendre un peu pour la capture
    await asyncio.sleep(2)
    
    # Vérifier qu'on a des frames
    frame = camera.get_latest_frame()
    assert frame is not None, "Aucun frame capturé"
    assert 'data' in frame, "Frame sans données"
    assert 'timestamp' in frame, "Frame sans timestamp"
    
    logging.info(f"✅ Frame capturé: {len(frame['data'])} bytes à {frame['timestamp']}")
    
    # Arrêter la capture
    camera.stop_capture()
    
    # Supprimer la caméra
    camera_manager.remove_camera("test_observer")
    
    logging.info("✅ Test de création de caméra réussi")

async def test_enhanced_rtsp_server():
    """Test du serveur RTSP amélioré avec streaming vidéo."""
    logging.info("🧪 Test du serveur RTSP amélioré")
    
    # Créer un utilisateur RTSP test
    test_user = CameraUser(
        id="test_user",
        name="TestObserver", 
        position=(40.0, 60.0, 90.0),
        rotation=(45.0, 0.0),
        rtsp_port=8558  # Port différent pour éviter les conflits
    )
    
    # Créer une caméra pour cet utilisateur
    camera = camera_manager.create_camera(
        observer_id=test_user.id,
        position=test_user.position,
        rotation=test_user.rotation,
        resolution=(320, 240)  # Résolution plus petite pour le test
    )
    
    # Créer le serveur RTSP amélioré
    rtsp_server = EnhancedRTSPServer(test_user, camera)
    
    try:
        # Démarrer le serveur
        await rtsp_server.start()
        logging.info(f"✅ Serveur RTSP amélioré démarré sur {test_user.rtsp_url}")
        
        # Laisser le serveur tourner un peu
        await asyncio.sleep(3)
        
        # Vérifier que la caméra capture des frames
        frame = camera.get_latest_frame()
        if frame:
            logging.info(f"✅ Caméra active: frame de {len(frame['data'])} bytes")
        else:
            logging.warning("⚠️  Aucun frame capturé par la caméra")
        
        logging.info("✅ Test du serveur RTSP amélioré réussi")
        
    except Exception as e:
        logging.error(f"❌ Erreur dans le test du serveur RTSP: {e}")
        raise
    finally:
        # Nettoyer
        await rtsp_server.stop()
        camera_manager.remove_camera(test_user.id)

async def test_multiple_cameras():
    """Test de multiples caméras simultanées."""
    logging.info("🧪 Test de multiples caméras simultanées")
    
    # Créer plusieurs caméras
    cameras = []
    for i in range(3):
        camera_id = f"multi_camera_{i}"
        camera = camera_manager.create_camera(
            observer_id=camera_id,
            position=(30.0 + i * 10, 50.0, 80.0 - i * 10),
            rotation=(i * 90.0, 0.0),
            resolution=(320, 240)
        )
        cameras.append((camera_id, camera))
        
    # Démarrer toutes les caméras (avec modèle du monde None pour le test)
    for camera_id, camera in cameras:
        camera.start_capture(None)  # Démarrer individuellement pour le test
    
    # Attendre un peu
    await asyncio.sleep(3)
    
    # Vérifier que toutes les caméras capturent
    active_cameras = 0
    for camera_id, camera in cameras:
        frame = camera.get_latest_frame()
        if frame:
            active_cameras += 1
            logging.info(f"✅ Caméra {camera_id}: {len(frame['data'])} bytes")
        else:
            logging.warning(f"⚠️  Caméra {camera_id}: pas de frame")
    
    assert active_cameras >= 3, f"Seulement {active_cameras}/3 caméras actives"
    
    # Nettoyer
    camera_manager.stop_all_cameras()
    for camera_id, _ in cameras:
        camera_manager.remove_camera(camera_id)
        
    logging.info("✅ Test de multiples caméras réussi")

async def test_camera_position_update():
    """Test de mise à jour de position de caméra."""
    logging.info("🧪 Test de mise à jour de position de caméra")
    
    # Créer une caméra
    camera = camera_manager.create_camera(
        observer_id="position_test",
        position=(10.0, 20.0, 30.0),
        rotation=(0.0, 0.0)
    )
    
    original_position = camera.position
    
    # Mettre à jour la position
    new_position = (50.0, 60.0, 70.0)
    new_rotation = (90.0, 45.0)
    camera.update_position(new_position, new_rotation)
    
    assert camera.position == new_position, f"Position non mise à jour: {camera.position} != {new_position}"
    assert camera.rotation == new_rotation, f"Rotation non mise à jour: {camera.rotation} != {new_rotation}"
    
    logging.info(f"✅ Position mise à jour: {original_position} -> {new_position}")
    
    # Nettoyer
    camera_manager.remove_camera("position_test")
    
    logging.info("✅ Test de mise à jour de position réussi")

async def main():
    """Exécute tous les tests du système de streaming caméra."""
    logging.info("🎯 Démarrage des tests du système de streaming caméra RTSP")
    
    try:
        # Test 1: Création de caméra basique
        await test_camera_creation()
        
        # Test 2: Serveur RTSP amélioré
        await test_enhanced_rtsp_server()
        
        # Test 3: Multiples caméras
        await test_multiple_cameras()
        
        # Test 4: Mise à jour de position
        await test_camera_position_update()
        
        logging.info("")
        logging.info("🎉 TOUS LES TESTS DE STREAMING RÉUSSIS!")
        logging.info("✅ Système de caméras d'observateurs fonctionnel")
        logging.info("✅ Serveurs RTSP améliorés avec streaming vidéo")
        logging.info("✅ Capture de frames depuis perspectives d'observateurs")
        logging.info("✅ Support multi-caméras simultanées")
        
        return 0
        
    except Exception as e:
        logging.error(f"❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))