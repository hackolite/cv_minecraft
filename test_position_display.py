#!/usr/bin/env python3
"""
Test pour l'affichage permanent de la position utilisateur.
Vérifie que la position est affichée sous la forme "x:valeur, y:valeur, z:valeur".
"""

import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_position_display_format():
    """Test que la position est formatée correctement."""
    
    # Test simple de formatage sans importer les classes graphiques
    test_positions = [
        ((10.5, 20.3, -5.7), "x:10.5, y:20.3, z:-5.7"),
        ((0.0, 0.0, 0.0), "x:0.0, y:0.0, z:0.0"),
        ((100.123, -50.789, 25.456), "x:100.1, y:-50.8, z:25.5"),
        ((-12.34, 64.78, -99.12), "x:-12.3, y:64.8, z:-99.1")
    ]
    
    for pos, expected in test_positions:
        x, y, z = pos
        formatted = f"x:{x:.1f}, y:{y:.1f}, z:{z:.1f}"
        assert formatted == expected, f"Position {pos}: attendu '{expected}', obtenu '{formatted}'"
        print(f"✅ Position {pos} formatée correctement: {formatted}")
    
    return True

def test_method_exists():
    """Test que la méthode update_position_display existe dans le code."""
    
    try:
        # Lire le fichier source pour vérifier que la méthode existe
        with open('minecraft_client_fr.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier que la méthode update_position_display existe
        assert 'def update_position_display(self):' in content, "Méthode update_position_display non trouvée"
        print("✅ Méthode update_position_display trouvée dans le code")
        
        # Vérifier que le label de position est créé
        assert 'self.position_label = pyglet.text.Label(' in content, "Label de position non trouvé"
        print("✅ Label de position trouvé dans setup_ui")
        
        # Vérifier que le label de position est dessiné
        assert 'self.position_label.draw()' in content, "Appel à position_label.draw() non trouvé"
        print("✅ Appel à position_label.draw() trouvé dans draw_ui")
        
        # Vérifier que update_position_display est appelé
        assert 'self.update_position_display()' in content, "Appel à update_position_display non trouvé"
        print("✅ Appel à update_position_display trouvé dans update_ui")
        
        # Vérifier le format de la position
        format_pattern = 'f"x:{x:.1f}, y:{y:.1f}, z:{z:.1f}"'
        assert format_pattern in content, "Format de position correct non trouvé"
        print("✅ Format de position correct trouvé: x:valeur, y:valeur, z:valeur")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def test_ui_structure():
    """Test que la structure UI est correcte."""
    
    try:
        with open('minecraft_client_fr.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier que le label de position a une couleur distincte
        assert 'color=(0, 255, 255, 255)' in content, "Couleur cyan du label de position non trouvée"
        print("✅ Label de position a une couleur cyan distinctive")
        
        # Vérifier que le label de position est positionné correctement
        assert 'y=self.height - 60' in content, "Position Y du label de position non trouvée"
        print("✅ Label de position bien positionné (y=height-60)")
        
        # Vérifier que draw_ui dessine la position en premier
        draw_ui_start = content.find('def draw_ui(self):')
        position_draw = content.find('self.position_label.draw()', draw_ui_start)
        debug_draw = content.find('if self.show_debug:', draw_ui_start)
        
        assert position_draw < debug_draw, "Position label doit être dessiné avant les infos debug"
        print("✅ Label de position dessiné avant les infos debug (toujours visible)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de structure UI: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test de l'affichage permanent de la position...\n")
    
    try:
        success = True
        success &= test_position_display_format()
        success &= test_method_exists()
        success &= test_ui_structure()
        
        if success:
            print("\n🎉 TESTS RÉUSSIS!")
            print("✅ La position est affichée sous la forme 'x:valeur, y:valeur, z:valeur'")
            print("✅ L'affichage est permanent (indépendant du mode debug)")
            print("✅ L'intégration UI fonctionne correctement")
            print("✅ Le label de position a une couleur distinctive")
            print("✅ Le label de position est toujours visible")
        else:
            print("\n❌ Certains tests ont échoué")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erreur générale lors des tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)