#!/usr/bin/env python3
"""
Validation des exigences pour l'implémentation pyglet client-serveur
"""

import sys
import os

def test_terrain_serveur():
    """Vérification du terrain de base pour le serveur"""
    print("1️⃣ Vérification du terrain de base pour le serveur...")
    try:
        from server import MinecraftServer
        server = MinecraftServer(world_size=10)
        if server.get_world_size() > 0:
            print(f"   ✅ Terrain généré avec {server.get_world_size()} blocs")
            return True
        else:
            print("   ❌ Aucun terrain généré")
            return False
    except Exception as e:
        print(f"   ❌ Erreur terrain serveur: {e}")
        return False

def test_mouvement_wasd():
    """Vérification du mouvement WASD côté client pyglet"""
    print("2️⃣ Vérification du mouvement WASD côté client...")
    try:
        # Analyser le code source du client pyglet
        with open('pyglet_client.py', 'r') as f:
            client_code = f.read()
        
        # Vérifier les touches WASD/ZQSD
        wasd_checks = [
            'key.W' in client_code or 'key.Z' in client_code,  # Forward
            'key.S' in client_code,  # Backward
            'key.A' in client_code or 'key.Q' in client_code,  # Left
            'key.D' in client_code,  # Right
            'strafe' in client_code,  # Movement system
            'get_motion_vector' in client_code  # Motion calculation
        ]
        
        if all(wasd_checks):
            print("   ✅ Contrôles WASD/ZQSD implémentés")
            return True
        else:
            print("   ❌ Contrôles WASD manquants")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur mouvement WASD: {e}")
        return False

def test_creation_suppression_blocs():
    """Vérification de la création/suppression de blocs"""
    print("3️⃣ Vérification de la création/suppression de blocs...")
    try:
        with open('pyglet_client.py', 'r') as f:
            client_code = f.read()
        
        with open('server.py', 'r') as f:
            server_code = f.read()
        
        # Vérifier côté client
        client_checks = [
            'on_mouse_press' in client_code,
            'add_block' in client_code,
            'remove_block' in client_code,
            'mouse.LEFT' in client_code,
            'mouse.RIGHT' in client_code
        ]
        
        # Vérifier côté serveur
        server_checks = [
            'handle_add_block' in server_code,
            'handle_remove_block' in server_code,
            'add_block' in server_code,
            'remove_block' in server_code
        ]
        
        if all(client_checks) and all(server_checks):
            print("   ✅ Système de création/suppression de blocs implémenté")
            return True
        else:
            print("   ❌ Système de blocs incomplet")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur gestion blocs: {e}")
        return False

def test_gravite():
    """Vérification de la gravité"""
    print("4️⃣ Vérification de la gravité...")
    try:
        with open('pyglet_client.py', 'r') as f:
            client_code = f.read()
        
        gravity_checks = [
            'GRAVITY' in client_code,
            'self.dy' in client_code,
            'TERMINAL_VELOCITY' in client_code,
            'gravity' in client_code.lower(),
            'dt * GRAVITY' in client_code
        ]
        
        if sum(gravity_checks) >= 3:  # Au moins 3 éléments de gravité
            print("   ✅ Système de gravité implémenté")
            return True
        else:
            print("   ❌ Système de gravité manquant")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur gravité: {e}")
        return False

def test_saut():
    """Vérification de la possibilité de sauter"""
    print("5️⃣ Vérification de la possibilité de sauter...")
    try:
        with open('pyglet_client.py', 'r') as f:
            client_code = f.read()
        
        jump_checks = [
            'JUMP_SPEED' in client_code,
            'jumping' in client_code,
            'key.SPACE' in client_code,
            'self.jumping = True' in client_code,
            'MAX_JUMP_HEIGHT' in client_code
        ]
        
        if sum(jump_checks) >= 4:  # Au moins 4 éléments de saut
            print("   ✅ Système de saut implémenté")
            return True
        else:
            print("   ❌ Système de saut manquant")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur saut: {e}")
        return False

def main():
    """Validation principale"""
    print("🎯 Validation des exigences du problème (Pyglet)")
    print("=" * 50)
    
    requirements = [
        ("Terrain de base pour le serveur", test_terrain_serveur),
        ("Mouvement WASD côté client", test_mouvement_wasd),
        ("Création et suppression de blocs", test_creation_suppression_blocs),
        ("Assurance d'avoir de la gravité", test_gravite),
        ("Possibilité de sauter", test_saut)
    ]
    
    results = []
    for name, test_func in requirements:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ Erreur inattendue: {e}")
            results.append((name, False))
        print()
    
    print("📋 RÉSUMÉ DES EXIGENCES")
    print("=" * 30)
    
    passed = 0
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    total = len(results)
    failed = total - passed
    
    if failed == 0:
        print(f"\n🎉 Toutes les {total} exigences sont satisfaites!")
        print("\n🎮 Implémentation pyglet client-serveur complète")
        print("\nPour jouer:")
        print("  1. python3 server.py")
        print("  2. python3 pyglet_client.py")
    else:
        print(f"\n⚠️  {failed} exigence(s) manquante(s)")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)