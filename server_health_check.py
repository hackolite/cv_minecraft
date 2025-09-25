#!/usr/bin/env python3
"""
Script de vérification de santé du serveur FastAPI
FastAPI Server Health Check Script

Ce script aide à diagnostiquer les problèmes de connexion au serveur FastAPI.
"""

import asyncio
import requests
import socket
import subprocess
import time
import sys
from typing import Optional, Dict, Any

def check_port_availability(host: str = "localhost", port: int = 8080) -> bool:
    """Vérifie si un port est disponible."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.connect_ex((host, port))
            return result != 0  # True si le port est libre
    except Exception:
        return False

def check_server_connection(host: str = "localhost", port: int = 8080, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Vérifie la connexion au serveur et récupère les informations de santé."""
    try:
        response = requests.get(f"http://{host}:{port}/health", timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection refused", "details": "Server not running or unreachable"}
    except requests.exceptions.Timeout:
        return {"error": "Timeout", "details": f"Server did not respond within {timeout} seconds"}
    except Exception as e:
        return {"error": "Unknown error", "details": str(e)}

def find_processes_using_port(port: int = 8080) -> list:
    """Trouve les processus utilisant un port donné."""
    try:
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        processes = []
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTEN' in line:
                processes.append(line.strip())
        return processes
    except Exception:
        return []

def suggest_solutions(error_type: str) -> list:
    """Suggère des solutions basées sur le type d'erreur."""
    solutions = {
        "Connection refused": [
            "1. Vérifiez que le serveur FastAPI est en cours d'exécution:",
            "   python demo_fastapi_cameras.py",
            "   ou",
            "   python server_with_cameras.py",
            "",
            "2. Si le serveur était déjà démarré, il peut avoir été arrêté. Redémarrez-le.",
            "",
            "3. Vérifiez les logs du serveur pour des erreurs de démarrage.",
        ],
        "Port occupied": [
            "1. Un autre processus utilise le port 8080. Options:",
            "   a) Arrêtez l'autre processus",
            "   b) Changez le port dans users_config.json",
            "   c) Le serveur trouvera automatiquement un port libre",
            "",
            "2. Pour voir les processus utilisant le port:",
            "   netstat -tlnp | grep :8080",
        ],
        "Timeout": [
            "1. Le serveur met du temps à démarrer. Attendez quelques secondes.",
            "",
            "2. Vérifiez les resources système (CPU, mémoire).",
            "",
            "3. Augmentez le timeout de connexion.",
        ]
    }
    return solutions.get(error_type, ["Erreur inconnue. Consultez les logs du serveur."])

def main():
    """Point d'entrée principal du script de diagnostic."""
    print("🔧 Diagnostic du Serveur FastAPI")
    print("=" * 40)
    print()
    
    host = "localhost"
    port = 8080
    
    # Étape 1: Vérifier la disponibilité du port
    print("1. Vérification du port...")
    port_available = check_port_availability(host, port)
    
    if port_available:
        print(f"   ❌ Port {port} est libre - le serveur n'est pas en cours d'exécution")
        error_type = "Connection refused"
    else:
        print(f"   ✅ Port {port} est occupé - un serveur écoute sur ce port")
        
        # Afficher les processus utilisant le port
        processes = find_processes_using_port(port)
        if processes:
            print("   Processus détectés:")
            for proc in processes[:3]:  # Limiter à 3 processus
                print(f"     {proc}")
    
    print()
    
    # Étape 2: Tester la connexion au serveur
    print("2. Test de connexion au serveur...")
    
    health_info = check_server_connection(host, port, timeout=10)
    
    if health_info and "error" not in health_info:
        print("   ✅ Serveur accessible et en bonne santé!")
        print(f"   📊 Caméras: {health_info.get('cameras_active', 0)}/{health_info.get('cameras_total', 0)} actives")
        print(f"   🌐 URL: {health_info.get('server', f'http://{host}:{port}')}")
        
        # Tester d'autres endpoints
        print("\n3. Test des endpoints principaux...")
        endpoints = [
            ("/", "Interface web"),
            ("/cameras", "API caméras"),
        ]
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"http://{host}:{port}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {description}: OK")
                else:
                    print(f"   ❌ {description}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {description}: {e}")
        
        print("\n🎉 Le serveur fonctionne correctement!")
        print(f"🌐 Accédez à http://{host}:{port} dans votre navigateur")
        
    else:
        error_type = health_info.get("error", "Unknown error") if health_info else "Connection refused"
        error_details = health_info.get("details", "") if health_info else ""
        
        print(f"   ❌ Erreur: {error_type}")
        if error_details:
            print(f"   Détails: {error_details}")
        
        if not port_available:
            error_type = "Port occupied"
        
        print(f"\n💡 Solutions suggérées pour '{error_type}':")
        solutions = suggest_solutions(error_type)
        for solution in solutions:
            print(f"   {solution}")
    
    print("\n" + "=" * 40)
    print("Diagnostic terminé.")

if __name__ == "__main__":
    main()