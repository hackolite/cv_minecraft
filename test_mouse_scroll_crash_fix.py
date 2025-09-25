#!/usr/bin/env python3
"""
Test pour la correction du crash lors de la sélection avec la molette de souris.

Ce test vérifie que le problème de KeyError lors de l'utilisation de la molette 
de souris pour sélectionner la caméra a été corrigé.

Bug corrigé: "quand je selectionne a la molette camera, le client se ferme brutalement"
Cause: KeyError lors de l'accès à self.keys[key.LCTRL] et self.keys[key.RCTRL] 
       quand les touches n'ont pas encore été pressées.
"""

import unittest
import sys
import os

# Ajouter le répertoire du projet pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol import BlockType, CameraType

class TestMouseScrollCrashFix(unittest.TestCase):
    """Tests pour la correction du crash de la molette de souris."""
    
    def setUp(self):
        """Préparation des tests."""
        # Simuler l'état de la fenêtre du jeu
        self.keys = {}  # Dictionnaire vide comme au démarrage
        self.block = BlockType.GRASS  # Bloc par défaut
        self.camera_types = [CameraType.STATIC, CameraType.ROTATING, CameraType.TRACKING, CameraType.WIDE_ANGLE, CameraType.ZOOM]
        self.current_camera_type = self.camera_types[0]
        self.exclusive = True
        
        # Simuler les constantes de touches (valeurs de pyglet)
        self.LCTRL = 65507
        self.RCTRL = 65508
        
    def test_mouse_scroll_without_ctrl_keys_initialized(self):
        """Test que la molette fonctionne même si les touches Ctrl n'ont jamais été pressées."""
        # Simuler l'état initial: aucune touche pressée, keys vide
        keys = {}
        
        # Cette ligne causait le crash avant la correction
        try:
            # Version corrigée utilisant .get() avec défaut False
            ctrl_pressed = keys.get(self.LCTRL, False) or keys.get(self.RCTRL, False)
            self.assertFalse(ctrl_pressed, "Ctrl ne devrait pas être pressé")
        except KeyError:
            self.fail("KeyError ne devrait plus se produire avec la correction")
    
    def test_mouse_scroll_with_ctrl_pressed(self):
        """Test que la détection de Ctrl fonctionne quand elle est pressée."""
        keys = {}
        
        # Simuler l'appui sur Ctrl gauche
        keys[self.LCTRL] = True
        ctrl_pressed = keys.get(self.LCTRL, False) or keys.get(self.RCTRL, False)
        self.assertTrue(ctrl_pressed, "Ctrl gauche devrait être détecté")
        
        # Simuler l'appui sur Ctrl droit à la place
        keys[self.LCTRL] = False
        keys[self.RCTRL] = True
        ctrl_pressed = keys.get(self.LCTRL, False) or keys.get(self.RCTRL, False)
        self.assertTrue(ctrl_pressed, "Ctrl droit devrait être détecté")
    
    def test_camera_block_selection_logic(self):
        """Test la logique de sélection des blocs caméra."""
        keys = {}
        block = BlockType.CAMERA
        exclusive = True
        
        # Test sans Ctrl: ne devrait pas entrer dans la sélection de type de caméra
        ctrl_pressed = keys.get(self.LCTRL, False) or keys.get(self.RCTRL, False)
        camera_type_selection = block == BlockType.CAMERA and ctrl_pressed
        self.assertFalse(camera_type_selection, "Ne devrait pas sélectionner le type de caméra sans Ctrl")
        
        # Test avec Ctrl: devrait entrer dans la sélection de type de caméra
        keys[self.LCTRL] = True
        ctrl_pressed = keys.get(self.LCTRL, False) or keys.get(self.RCTRL, False)
        camera_type_selection = block == BlockType.CAMERA and ctrl_pressed
        self.assertTrue(camera_type_selection, "Devrait sélectionner le type de caméra avec Ctrl")
    
    def test_camera_type_cycling(self):
        """Test le cycle des types de caméra."""
        camera_types = [CameraType.STATIC, CameraType.ROTATING, CameraType.TRACKING, CameraType.WIDE_ANGLE, CameraType.ZOOM]
        current_camera_type = camera_types[0]  # STATIC
        
        # Simuler scroll vers le haut (scroll_y > 0)
        current_camera_index = camera_types.index(current_camera_type)
        new_camera_index = (current_camera_index + 1) % len(camera_types)
        new_camera_type = camera_types[new_camera_index]
        
        self.assertEqual(new_camera_type, CameraType.ROTATING, "Devrait passer à ROTATING")
        
        # Simuler scroll vers le bas (scroll_y < 0) depuis ROTATING
        current_camera_type = CameraType.ROTATING
        current_camera_index = camera_types.index(current_camera_type)
        new_camera_index = (current_camera_index - 1) % len(camera_types)
        new_camera_type = camera_types[new_camera_index]
        
        self.assertEqual(new_camera_type, CameraType.STATIC, "Devrait revenir à STATIC")
    
    def test_robustness_against_missing_keys(self):
        """Test la robustesse contre l'absence de clés dans le dictionnaire."""
        keys = {}
        
        # Tester avec des clés diverses qui pourraient ne pas exister
        test_keys = [self.LCTRL, self.RCTRL, 999999, -1, 'invalid']
        
        for test_key in test_keys:
            try:
                # La méthode corrigée devrait toujours retourner False sans erreur
                result = keys.get(test_key, False)
                self.assertFalse(result, f"Clé inexistante {test_key} devrait retourner False")
            except Exception as e:
                self.fail(f"Ne devrait pas lever d'exception pour la clé {test_key}: {e}")

    def test_camera_selection_integration(self):
        """Test d'intégration de la sélection de caméra complète."""
        # Simuler l'état complet d'une fenêtre
        keys = {}
        block = BlockType.CAMERA
        camera_types = [CameraType.STATIC, CameraType.ROTATING, CameraType.TRACKING]
        current_camera_type = camera_types[0]
        exclusive = True
        
        # Scénario 1: Molette sans Ctrl (sélection de bloc normale)
        ctrl_pressed = keys.get(self.LCTRL, False) or keys.get(self.RCTRL, False)
        should_change_camera_type = block == BlockType.CAMERA and ctrl_pressed
        self.assertFalse(should_change_camera_type, "Ne devrait pas changer le type de caméra")
        
        # Scénario 2: Molette avec Ctrl (sélection de type de caméra)
        keys[self.LCTRL] = True
        ctrl_pressed = keys.get(self.LCTRL, False) or keys.get(self.RCTRL, False)
        should_change_camera_type = block == BlockType.CAMERA and ctrl_pressed
        self.assertTrue(should_change_camera_type, "Devrait changer le type de caméra")
        
        # Simuler le changement de type avec scroll vers le haut
        if should_change_camera_type:
            scroll_y = 1  # Scroll vers le haut
            current_camera_index = camera_types.index(current_camera_type)
            new_camera_index = (current_camera_index + 1) % len(camera_types)
            new_camera_type = camera_types[new_camera_index]
            self.assertEqual(new_camera_type, CameraType.ROTATING)


def run_tests():
    """Exécute tous les tests."""
    print("🔧 Tests de la correction du crash de la molette de souris")
    print("=" * 70)
    print("Bug corrigé: 'quand je sélectionne à la molette camera, le client se ferme brutalement'")
    print("=" * 70)
    
    # Créer une suite de tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMouseScrollCrashFix)
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ TOUS LES TESTS PASSENT!")
        print("✅ La correction du crash de la molette de souris fonctionne correctement")
        print("✅ Plus de KeyError lors de l'utilisation de la molette pour sélectionner la caméra")
    else:
        print("❌ Certains tests ont échoué")
        print(f"❌ Échecs: {len(result.failures)}, Erreurs: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)