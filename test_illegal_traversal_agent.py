#!/usr/bin/env python3
"""
Test pour l'agent de détection de traversée illégale de blocs.
Vérifie que l'agent détecte correctement les traversées et log selon le format requis.
"""

import logging
import sys
import os
import io
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from illegal_traversal_agent import IllegalBlockTraversalAgent


def setup_logging_capture():
    """Configure le logging pour capturer les logs de traversée illégale."""
    # Créer un buffer pour capturer les logs
    log_capture = io.StringIO()
    
    # Créer un handler pour le logger de traversée
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Obtenir le logger de traversée et ajouter notre handler
    traversal_logger = logging.getLogger('illegal_traversal')
    traversal_logger.setLevel(logging.INFO)
    traversal_logger.addHandler(handler)
    
    return log_capture, traversal_logger


def test_illegal_traversal_detection():
    """Test de détection de traversée illégale."""
    print("🧪 Test de détection de traversée illégale de blocs")
    
    # Setup logging capture
    log_capture, traversal_logger = setup_logging_capture()
    
    # Créer un monde avec un bloc solide
    world = {(10, 10, 10): 'stone'}
    agent = IllegalBlockTraversalAgent(world)
    
    # Test de traversée: joueur passe d'une position valide à l'intérieur d'un bloc
    old_position = (9.0, 10.0, 10.0)  # Position valide
    new_position = (10.5, 10.5, 10.5)  # Position à l'intérieur du bloc stone
    
    # Vérifier que la traversée est détectée
    result = agent.check_traversal("player123", "TestPlayer", old_position, new_position)
    
    # Vérifier le résultat
    assert result == True, "Should detect illegal traversal"
    
    # Obtenir les logs capturés
    log_output = log_capture.getvalue()
    print("Logs capturés:")
    print(log_output)
    
    # Vérifier le format des logs selon les exigences
    assert "WARNING" in log_output, "Should have WARNING level log"
    assert "🚨 ILLEGAL BLOCK TRAVERSAL" in log_output, "Should have illegal traversal warning"
    assert "Player TestPlayer (player123)" in log_output, "Should include player name and ID"
    assert "traversed solid block" in log_output, "Should mention traversed solid block"
    assert "(10, 10, 10)" in log_output, "Should include block position"
    assert "Old position:" in log_output, "Should log old position"
    assert "New position:" in log_output, "Should log new position"
    assert "Block type: stone" in log_output, "Should log block type"
    assert str(old_position) in log_output, "Should include old position values"
    assert str(new_position) in log_output, "Should include new position values"
    
    print("✅ Test de détection de traversée: RÉUSSI")
    return True


def test_no_traversal_no_detection():
    """Test qu'aucune traversée = aucune détection."""
    print("\n🧪 Test qu'aucune traversée = aucune détection")
    
    # Setup logging capture
    log_capture, traversal_logger = setup_logging_capture()
    
    # Créer un monde avec un bloc solide
    world = {(10, 10, 10): 'stone'}
    agent = IllegalBlockTraversalAgent(world)
    
    # Test de mouvement valide: joueur reste dans l'air
    old_position = (9.0, 10.0, 10.0)  # Position valide
    new_position = (8.0, 10.0, 10.0)  # Autre position valide
    
    # Vérifier qu'aucune traversée n'est détectée
    result = agent.check_traversal("player123", "TestPlayer", old_position, new_position)
    
    # Vérifier le résultat
    assert result == False, "Should not detect traversal for valid movement"
    
    # Obtenir les logs capturés
    log_output = log_capture.getvalue()
    print(f"Logs capturés (devrait être vide): '{log_output}'")
    
    # Vérifier qu'aucun log n'est généré
    assert log_output.strip() == "", "Should not log when no traversal"
    
    print("✅ Test aucune traversée: RÉUSSI")
    return True


def test_disconnection_logging():
    """Test du logging de déconnexion."""
    print("\n🧪 Test du logging de déconnexion")
    
    # Setup logging capture
    log_capture, traversal_logger = setup_logging_capture()
    
    # Créer un agent
    world = {(10, 10, 10): 'stone'}
    agent = IllegalBlockTraversalAgent(world)
    
    # Test du logging de déconnexion
    agent.log_disconnection("player123", "TestPlayer")
    
    # Obtenir les logs capturés
    log_output = log_capture.getvalue()
    print("Logs capturés:")
    print(log_output)
    
    # Vérifier le format du log de déconnexion
    assert "INFO" in log_output, "Should have INFO level log"
    assert "Player TestPlayer (player123) disconnected for illegal block traversal." in log_output, "Should log disconnection with specific message"
    
    print("✅ Test de logging de déconnexion: RÉUSSI")
    return True


def test_different_block_types():
    """Test avec différents types de blocs."""
    print("\n🧪 Test avec différents types de blocs")
    
    # Setup logging capture
    log_capture, traversal_logger = setup_logging_capture()
    
    # Créer un monde avec différents types de blocs
    world = {
        (10, 10, 10): 'grass',
        (11, 10, 10): 'wood',
        (12, 10, 10): 'air'  # Ne devrait pas déclencher de traversée
    }
    agent = IllegalBlockTraversalAgent(world)
    
    # Test avec bloc grass
    result = agent.check_traversal("player1", "Player1", (9.0, 10.0, 10.0), (10.5, 10.5, 10.5))
    assert result == True, "Should detect traversal of grass block"
    
    # Test avec bloc wood
    result = agent.check_traversal("player2", "Player2", (10.0, 10.0, 10.0), (11.5, 10.5, 10.5))
    assert result == True, "Should detect traversal of wood block"
    
    # Test avec bloc air (ne devrait pas déclencher)
    result = agent.check_traversal("player3", "Player3", (11.0, 10.0, 10.0), (12.5, 10.5, 10.5))
    assert result == False, "Should not detect traversal of air block"
    
    # Vérifier les logs
    log_output = log_capture.getvalue()
    assert "Block type: grass" in log_output, "Should log grass block type"
    assert "Block type: wood" in log_output, "Should log wood block type"
    
    print("✅ Test avec différents types de blocs: RÉUSSI")
    return True


def main():
    """Exécute tous les tests de l'agent de traversée illégale."""
    print("🚀 Tests de l'agent de détection de traversée illégale - Minecraft CV")
    print("=" * 80)
    
    try:
        # Test de détection de traversée illégale
        test_illegal_traversal_detection()
        
        # Test qu'aucune traversée = aucune détection
        test_no_traversal_no_detection()
        
        # Test du logging de déconnexion
        test_disconnection_logging()
        
        # Test avec différents types de blocs
        test_different_block_types()
        
        print("\n" + "=" * 80)
        print("✅ TOUS LES TESTS PASSENT!")
        print("✅ L'agent de détection de traversée illégale fonctionne correctement")
        print("✅ Les logs respectent le format requis")
        print("✅ La déconnexion est correctement loggée")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)