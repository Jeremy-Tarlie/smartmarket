#!/usr/bin/env python3
"""
Script de test pour les fonctionnalités du Jour 4.
"""

import os
import sys
import time
import requests
import json
import websocket
import threading
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/admin/orders/"

def test_health_checks():
    """Test des health checks."""
    print("🔍 Test des health checks...")
    
    # Test health live
    try:
        response = requests.get(f"{BASE_URL}/health/live/", timeout=10)
        if response.status_code == 200:
            print("✅ Health live: OK")
        else:
            print(f"❌ Health live: {response.status_code}")
    except Exception as e:
        print(f"❌ Health live: {e}")
    
    # Test health ready
    try:
        response = requests.get(f"{BASE_URL}/health/ready/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health ready: OK")
            print(f"   - Database: {data.get('checks', {}).get('database', 'Unknown')}")
            print(f"   - Redis: {data.get('checks', {}).get('redis', 'Unknown')}")
            print(f"   - Channels: {data.get('checks', {}).get('channels', 'Unknown')}")
        else:
            print(f"❌ Health ready: {response.status_code}")
    except Exception as e:
        print(f"❌ Health ready: {e}")

def test_celery_tasks():
    """Test des tâches Celery."""
    print("\n🔧 Test des tâches Celery...")
    
    # Test de la tâche de debug
    try:
        response = requests.post(f"{BASE_URL}/api/v1/test-celery/", timeout=30)
        if response.status_code == 200:
            print("✅ Tâche Celery: OK")
        else:
            print(f"❌ Tâche Celery: {response.status_code}")
    except Exception as e:
        print(f"❌ Tâche Celery: {e}")

def test_websocket_connection():
    """Test de la connexion WebSocket."""
    print("\n🌐 Test de la connexion WebSocket...")
    
    messages_received = []
    
    def on_message(ws, message):
        messages_received.append(json.loads(message))
        print(f"📨 Message reçu: {message[:100]}...")
    
    def on_error(ws, error):
        print(f"❌ Erreur WebSocket: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print("🔌 Connexion WebSocket fermée")
    
    def on_open(ws):
        print("✅ Connexion WebSocket établie")
        # Envoyer un ping
        ws.send(json.dumps({"type": "ping"}))
    
    try:
        ws = websocket.WebSocketApp(
            WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Lancer la connexion dans un thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Attendre un peu pour recevoir des messages
        time.sleep(5)
        
        # Fermer la connexion
        ws.close()
        
        if messages_received:
            print(f"✅ WebSocket: {len(messages_received)} messages reçus")
        else:
            print("⚠️ WebSocket: Aucun message reçu")
            
    except Exception as e:
        print(f"❌ WebSocket: {e}")

def test_api_endpoints():
    """Test des endpoints API."""
    print("\n🔗 Test des endpoints API...")
    
    endpoints = [
        "/api/v1/products/",
        "/api/v1/categories/",
        "/health/live/",
        "/health/ready/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code in [200, 401, 403]:  # 401/403 sont OK pour les endpoints protégés
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_admin_dashboard():
    """Test du tableau de bord admin."""
    print("\n📊 Test du tableau de bord admin...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/dashboard/", timeout=10)
        if response.status_code in [200, 302]:  # 302 = redirection vers login
            print("✅ Tableau de bord admin: Accessible")
        else:
            print(f"❌ Tableau de bord admin: {response.status_code}")
    except Exception as e:
        print(f"❌ Tableau de bord admin: {e}")

def test_ml_endpoints():
    """Test des endpoints ML."""
    print("\n🤖 Test des endpoints ML...")
    
    ml_endpoints = [
        "/api/v1/ml/status/",
    ]
    
    for endpoint in ml_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code in [200, 401, 403]:
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def main():
    """Fonction principale de test."""
    print("🧪 TEST DES FONCTIONNALITÉS JOUR 4 - SMARTMARKET")
    print("=" * 60)
    print(f"🕐 Début des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL de base: {BASE_URL}")
    print()
    
    # Tests
    test_health_checks()
    test_api_endpoints()
    test_ml_endpoints()
    test_admin_dashboard()
    test_websocket_connection()
    test_celery_tasks()
    
    print("\n" + "=" * 60)
    print("🎉 Tests terminés!")
    print(f"🕐 Fin des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📋 Instructions pour les tests manuels:")
    print("1. Ouvrir http://localhost:8000/admin/dashboard/ dans un navigateur")
    print("2. Se connecter avec un compte admin")
    print("3. Créer une commande pour tester les notifications temps réel")
    print("4. Vérifier les logs Celery: docker-compose logs worker")
    print("5. Tester les health checks: curl http://localhost/health/ready/")

if __name__ == "__main__":
    main()

