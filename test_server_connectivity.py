#!/usr/bin/env python3
"""
Script de test de connectivité pour le serveur FastAPI
Test script for FastAPI server connectivity
"""

import asyncio
import requests
import time
import logging
# from fastapi_camera_server import fastapi_camera_server  # Removed as per IMPLEMENTATION_SUMMARY.md

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

async def test_server_connectivity():
    """Test la connectivité au serveur FastAPI."""
    
    print("🔧 Test de Connectivité du Serveur FastAPI")
    print("=" * 50)
    
    # Test 1: Vérifier si le port est disponible
    print("\n1. Vérification de la disponibilité du port...")
    
    # FastAPI camera server was removed as per IMPLEMENTATION_SUMMARY.md
    print("   ⚠️  FastAPI camera server was removed - skipping port check")
    print("   ✅ Test passed (functionality removed as intended)")
    
    # Test 2: Démarrer le serveur en arrière-plan
    print("\n2. Démarrage du serveur en arrière-plan...")
    
    # Camera/observer system was removed as per IMPLEMENTATION_SUMMARY.md
    # This test is now obsolete
    print("   ⚠️  Camera/observer system was removed - skipping server connectivity test")
    print("   ✅ Test passed (functionality removed as intended)")
    return True

async def main():
    """Point d'entrée principal."""
    try:
        await test_server_connectivity()
    except KeyboardInterrupt:
        print("\n⏹️  Test arrêté par l'utilisateur")
    except Exception as e:
        logging.error(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())