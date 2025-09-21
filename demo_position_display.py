#!/usr/bin/env python3
"""
Démonstration de l'affichage permanent de la position utilisateur.
Montre comment la position est affichée dans l'interface.
"""

import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_position_display():
    """Démontre l'affichage de position avec différentes valeurs."""
    
    print("🎮 Démonstration de l'affichage permanent de la position\n")
    print("Format utilisé: x:valeur, y:valeur, z:valeur")
    print("Couleur: Cyan (0, 255, 255, 255)")
    print("Position: Haut gauche de l'écran (x=10, y=height-60)")
    print("Visibilité: Toujours visible (indépendant du mode debug)\n")
    
    # Exemples de positions et leur affichage
    test_positions = [
        (30.0, 50.0, 80.0, "Position de spawn typique"),
        (0.0, 64.0, 0.0, "Position au centre du monde"),
        (-125.7, 12.3, 456.8, "Position avec coordonnées négatives"),
        (999.123, -45.678, 0.0, "Position avec haute précision"),
        (1.0, 100.5, -1.0, "Position simple près de l'origine")
    ]
    
    print("Exemples d'affichage de position:")
    print("-" * 50)
    
    for x, y, z, description in test_positions:
        display_text = f"x:{x:.1f}, y:{y:.1f}, z:{z:.1f}"
        print(f"{description:<35} → {display_text}")
    
    print("-" * 50)
    print("\n✅ Avantages de ce système:")
    print("  • Toujours visible, même sans mode debug")
    print("  • Format clair et concis")
    print("  • Couleur distincte pour éviter la confusion")
    print("  • Position fixe qui ne gêne pas le gameplay")
    print("  • Mise à jour automatique du mouvement")
    
    print("\n📍 Intégration dans l'interface:")
    print("  • setup_ui(): Création du label de position")
    print("  • update_position_display(): Mise à jour du texte")
    print("  • update_ui(): Appel automatique de la mise à jour")
    print("  • draw_ui(): Rendu permanent du label")

def demo_ui_structure():
    """Démontre la structure de l'interface utilisateur."""
    
    print("\n🖥️  Structure de l'interface utilisateur:")
    print("┌" + "─" * 58 + "┐")
    print("│ position_label (cyan): x:30.0, y:50.0, z:80.0          │")
    print("│ debug_label (blanc): Minecraft Client v1.0...          │")
    print("│                                                        │")
    print("│                        [viseur]                        │")
    print("│                                                        │")
    print("│                                                        │")
    print("│              message_label (jaune): Message...         │")
    print("└" + "─" * 58 + "┘")
    
    print("\nOrdre de rendu (draw_ui):")
    print("1. position_label.draw()     ← Toujours visible")
    print("2. debug_label.draw()        ← Seulement si show_debug=True")
    print("3. message_label.draw()      ← Messages temporaires")
    print("4. reticle.draw()            ← Viseur central")

if __name__ == "__main__":
    try:
        demo_position_display()
        demo_ui_structure()
        
        print("\n🎉 Démonstration terminée avec succès!")
        print("✅ La position utilisateur est maintenant affichée en permanence")
        print("✅ Format: x:valeur, y:valeur, z:valeur")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)