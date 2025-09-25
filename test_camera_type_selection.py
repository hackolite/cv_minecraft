#!/usr/bin/env python3
"""
Test Camera Type Selection - Test de la sélection du type de caméra
==================================================================

Tests unitaires pour vérifier le fonctionnement de la sélection 
du type de caméra avec la molette de souris.
"""

import unittest
from protocol import BlockType, CameraType

class TestCameraTypeSelection(unittest.TestCase):
    """Tests pour la sélection du type de caméra."""
    
    def setUp(self):
        """Préparation des tests."""
        # Mock window state for testing
        self.inventory = [BlockType.BRICK, BlockType.GRASS, BlockType.SAND, BlockType.STONE, BlockType.CAMERA]
        self.block = self.inventory[0]
        self.camera_types = [CameraType.STATIC, CameraType.ROTATING, CameraType.TRACKING, CameraType.WIDE_ANGLE, CameraType.ZOOM]
        self.current_camera_type = self.camera_types[0]
        self.keys = {65507: False, 65508: False}  # LCTRL, RCTRL
        self.exclusive = True
        self.messages = []
    
    def get_camera_type_name(self, camera_type):
        """Retourne le nom français du type de caméra."""
        names = {
            CameraType.STATIC: "Statique",
            CameraType.ROTATING: "Rotative",
            CameraType.TRACKING: "Poursuite",
            CameraType.WIDE_ANGLE: "Grand Angle",
            CameraType.ZOOM: "Zoom"
        }
        return names.get(camera_type, camera_type)
    
    def show_message(self, message):
        """Mock message handler."""
        self.messages.append(message)
    
    def simulate_mouse_scroll(self, scroll_y, ctrl_pressed=False):
        """Simulate the mouse scroll handler logic"""
        if not self.exclusive:
            return
            
        # Set ctrl key state
        self.keys[65507] = ctrl_pressed  # LCTRL
        
        # Camera type selection when camera block is selected and Ctrl is pressed
        if self.block == BlockType.CAMERA and (self.keys[65507] or self.keys[65508]):
            current_camera_index = self.camera_types.index(self.current_camera_type) if self.current_camera_type in self.camera_types else 0
            
            if scroll_y > 0:  # Scroll up
                new_camera_index = (current_camera_index + 1) % len(self.camera_types)
            elif scroll_y < 0:  # Scroll down  
                new_camera_index = (current_camera_index - 1) % len(self.camera_types)
            else:
                return
            
            self.current_camera_type = self.camera_types[new_camera_index]
            self.show_message(f"Type de caméra: {self.get_camera_type_name(self.current_camera_type)}")
            return
        
        # Normal block selection
        current_index = self.inventory.index(self.block) if self.block in self.inventory else 0
        
        if scroll_y > 0:  # Scroll up
            new_index = (current_index + 1) % len(self.inventory)
        elif scroll_y < 0:  # Scroll down
            new_index = (current_index - 1) % len(self.inventory)
        else:
            return
        
        old_block = self.block
        self.block = self.inventory[new_index]
        message = f"Bloc sélectionné: {self.block}"
        
        if self.block == BlockType.CAMERA:
            message += f" (Type: {self.get_camera_type_name(self.current_camera_type)})"
            message += " - Ctrl+Molette pour changer le type"
        
        self.show_message(message)
    
    def test_camera_types_exist(self):
        """Test que tous les types de caméra existent."""
        self.assertTrue(hasattr(CameraType, 'STATIC'))
        self.assertTrue(hasattr(CameraType, 'ROTATING'))
        self.assertTrue(hasattr(CameraType, 'TRACKING'))
        self.assertTrue(hasattr(CameraType, 'WIDE_ANGLE'))
        self.assertTrue(hasattr(CameraType, 'ZOOM'))
        
        self.assertEqual(CameraType.STATIC, 'static')
        self.assertEqual(CameraType.ROTATING, 'rotating')
        self.assertEqual(CameraType.TRACKING, 'tracking')
        self.assertEqual(CameraType.WIDE_ANGLE, 'wide_angle')
        self.assertEqual(CameraType.ZOOM, 'zoom')
    
    def test_camera_type_names(self):
        """Test la traduction des noms de types de caméra."""
        self.assertEqual(self.get_camera_type_name(CameraType.STATIC), "Statique")
        self.assertEqual(self.get_camera_type_name(CameraType.ROTATING), "Rotative")
        self.assertEqual(self.get_camera_type_name(CameraType.TRACKING), "Poursuite")
        self.assertEqual(self.get_camera_type_name(CameraType.WIDE_ANGLE), "Grand Angle")
        self.assertEqual(self.get_camera_type_name(CameraType.ZOOM), "Zoom")
    
    def test_normal_block_selection(self):
        """Test la sélection normale de blocs avec la molette."""
        # Start with brick
        self.assertEqual(self.block, BlockType.BRICK)
        
        # Scroll up to grass
        self.simulate_mouse_scroll(1)
        self.assertEqual(self.block, BlockType.GRASS)
        self.assertIn("Bloc sélectionné: grass", self.messages[-1])
        
        # Scroll down back to brick
        self.simulate_mouse_scroll(-1)
        self.assertEqual(self.block, BlockType.BRICK)
        self.assertIn("Bloc sélectionné: brick", self.messages[-1])
    
    def test_camera_block_selection(self):
        """Test la sélection du bloc caméra."""
        # Navigate to camera block
        while self.block != BlockType.CAMERA:
            self.simulate_mouse_scroll(1)
        
        self.assertEqual(self.block, BlockType.CAMERA)
        # Should show camera type and help message
        last_message = self.messages[-1]
        self.assertIn("camera", last_message)
        self.assertIn("Statique", last_message)  # Default camera type
        self.assertIn("Ctrl+Molette", last_message)
    
    def test_camera_type_selection_with_ctrl(self):
        """Test la sélection du type de caméra avec Ctrl+Molette."""
        # Select camera block first
        self.block = BlockType.CAMERA
        
        # Initial camera type should be static
        self.assertEqual(self.current_camera_type, CameraType.STATIC)
        
        # Ctrl+Scroll up should go to next camera type
        self.simulate_mouse_scroll(1, ctrl_pressed=True)
        self.assertEqual(self.current_camera_type, CameraType.ROTATING)
        self.assertIn("Type de caméra: Rotative", self.messages[-1])
        
        # Ctrl+Scroll up again
        self.simulate_mouse_scroll(1, ctrl_pressed=True)
        self.assertEqual(self.current_camera_type, CameraType.TRACKING)
        self.assertIn("Type de caméra: Poursuite", self.messages[-1])
        
        # Ctrl+Scroll down should go to previous
        self.simulate_mouse_scroll(-1, ctrl_pressed=True)
        self.assertEqual(self.current_camera_type, CameraType.ROTATING)
        self.assertIn("Type de caméra: Rotative", self.messages[-1])
    
    def test_camera_type_cycling(self):
        """Test le cycle complet des types de caméra."""
        self.block = BlockType.CAMERA
        initial_type = self.current_camera_type
        
        # Cycle through all camera types
        expected_sequence = [CameraType.ROTATING, CameraType.TRACKING, CameraType.WIDE_ANGLE, CameraType.ZOOM, CameraType.STATIC]
        
        for expected_type in expected_sequence:
            self.simulate_mouse_scroll(1, ctrl_pressed=True)
            self.assertEqual(self.current_camera_type, expected_type)
        
        # Should be back to initial type
        self.assertEqual(self.current_camera_type, initial_type)
    
    def test_no_camera_type_change_without_ctrl(self):
        """Test qu'on ne peut pas changer le type de caméra sans Ctrl."""
        self.block = BlockType.CAMERA
        initial_type = self.current_camera_type
        initial_messages = len(self.messages)
        
        # Scroll without Ctrl should change blocks, not camera type
        self.simulate_mouse_scroll(1, ctrl_pressed=False)
        
        # Should have moved to next block in inventory (brick)
        self.assertEqual(self.block, BlockType.BRICK)
        self.assertEqual(self.current_camera_type, initial_type)  # Camera type unchanged
        self.assertGreater(len(self.messages), initial_messages)  # New message generated
    
    def test_no_camera_type_change_without_camera_block(self):
        """Test qu'on ne peut pas changer le type de caméra sans bloc caméra sélectionné."""
        self.block = BlockType.STONE  # Not camera block
        initial_type = self.current_camera_type
        
        # Ctrl+Scroll should change blocks, not camera type
        self.simulate_mouse_scroll(1, ctrl_pressed=True)
        
        # Should have moved to next block
        self.assertEqual(self.block, BlockType.CAMERA)
        self.assertEqual(self.current_camera_type, initial_type)  # Camera type unchanged


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)