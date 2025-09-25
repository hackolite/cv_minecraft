#!/usr/bin/env python3
"""
Test Camera Blocks - Test des blocs caméra
==========================================

Tests unitaires pour vérifier le fonctionnement des blocs caméra.
"""

import unittest
import time
from protocol import BlockType
from camera_user_manager import camera_manager

class TestCameraBlocks(unittest.TestCase):
    """Tests pour les blocs caméra."""
    
    def setUp(self):
        """Préparation des tests."""
        # Nettoyer les caméras existantes
        for camera_id in list(camera_manager.cameras.keys()):
            camera = camera_manager.cameras[camera_id]
            camera_manager.remove_camera_user(camera.position)
    
    def test_camera_block_type_exists(self):
        """Test que le type de bloc CAMERA existe."""
        self.assertTrue(hasattr(BlockType, 'CAMERA'))
        self.assertEqual(BlockType.CAMERA, 'camera')
        
    def test_camera_manager_initialization(self):
        """Test l'initialisation du gestionnaire de caméras."""
        self.assertIsNotNone(camera_manager)
        self.assertEqual(len(camera_manager.cameras), 0)
        self.assertEqual(len(camera_manager.used_ports), 0)
        
    def test_camera_id_generation(self):
        """Test la génération d'IDs de caméra."""
        position = (10, 20, 30)
        camera_id = camera_manager.generate_camera_id(position)
        expected_id = "Camera_10_20_30"
        self.assertEqual(camera_id, expected_id)
        
    def test_port_allocation(self):
        """Test l'allocation des ports."""
        port1 = camera_manager.get_next_port()
        camera_manager.used_ports.add(port1)
        
        port2 = camera_manager.get_next_port()
        self.assertNotEqual(port1, port2)
        self.assertTrue(port2 > port1)
        
    def test_camera_creation_basic(self):
        """Test la création basique d'une caméra."""
        position = (50, 60, 70)
        
        # Vérifier qu'aucune caméra n'existe à cette position
        self.assertIsNone(camera_manager.get_camera_at_position(position))
        
        # Créer une caméra
        camera = camera_manager.create_camera_user(position)
        
        # Vérifier la création
        self.assertIsNotNone(camera)
        self.assertEqual(camera.position, position)
        self.assertEqual(camera.id, "Camera_50_60_70")
        self.assertGreaterEqual(camera.port, 8081)
        
        # Vérifier qu'elle est dans le gestionnaire
        stored_camera = camera_manager.get_camera_at_position(position)
        self.assertIsNotNone(stored_camera)
        self.assertEqual(stored_camera.id, camera.id)
        
    def test_camera_removal(self):
        """Test la suppression d'une caméra."""
        position = (80, 90, 100)
        
        # Créer une caméra
        camera = camera_manager.create_camera_user(position)
        self.assertIsNotNone(camera)
        
        # Vérifier qu'elle existe
        self.assertIsNotNone(camera_manager.get_camera_at_position(position))
        
        # Supprimer la caméra
        success = camera_manager.remove_camera_user(position)
        self.assertTrue(success)
        
        # Vérifier qu'elle n'existe plus
        self.assertIsNone(camera_manager.get_camera_at_position(position))
        
    def test_camera_list(self):
        """Test l'obtention de la liste des caméras."""
        # Au début, aucune caméra
        cameras = camera_manager.get_cameras()
        self.assertEqual(len(cameras), 0)
        
        # Créer quelques caméras
        positions = [(10, 20, 30), (40, 50, 60)]
        for position in positions:
            camera_manager.create_camera_user(position)
            
        # Vérifier la liste
        cameras = camera_manager.get_cameras()
        self.assertEqual(len(cameras), 2)
        
        # Vérifier le contenu des informations de caméra
        for camera_info in cameras:
            self.assertIn('id', camera_info)
            self.assertIn('position', camera_info)
            self.assertIn('port', camera_info)
            self.assertIn('running', camera_info)
            self.assertIn('url', camera_info)
            self.assertIn('view_endpoint', camera_info)
            
    def test_duplicate_camera_creation(self):
        """Test la création de caméras dupliquées."""
        position = (15, 25, 35)
        
        # Créer la première caméra
        camera1 = camera_manager.create_camera_user(position)
        self.assertIsNotNone(camera1)
        
        # Essayer de créer une caméra à la même position
        camera2 = camera_manager.create_camera_user(position)
        
        # Doit retourner la caméra existante
        self.assertEqual(camera1.id, camera2.id)
        
        # Vérifier qu'il n'y a qu'une seule caméra
        cameras = camera_manager.get_cameras()
        self.assertEqual(len(cameras), 1)

if __name__ == '__main__':
    # Exécuter les tests
    unittest.main(verbosity=2)