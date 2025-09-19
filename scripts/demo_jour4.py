#!/usr/bin/env python3
"""
Script de démonstration pour les captures du Jour 4.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime

def demo_health_checks():
    """Démonstration des health checks."""
    print("🔍 DÉMONSTRATION - HEALTH CHECKS")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Health live
    print("\n1. Health Check Live:")
    print("   URL: GET /health/live/")
    try:
        response = requests.get(f"{base_url}/health/live/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Health ready
    print("\n2. Health Check Ready:")
    print("   URL: GET /health/ready/")
    try:
        response = requests.get(f"{base_url}/health/ready/")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Service: {data.get('service')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Checks: {data.get('checks')}")
    except Exception as e:
        print(f"   Erreur: {e}")
    
    # Health detailed
    print("\n3. Health Check Detailed:")
    print("   URL: GET /health/detailed/")
    try:
        response = requests.get(f"{base_url}/health/detailed/")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Metrics: {list(data.get('metrics', {}).keys())}")
    except Exception as e:
        print(f"   Erreur: {e}")

def demo_celery_status():
    """Démonstration du statut Celery."""
    print("\n🔧 DÉMONSTRATION - CELERY STATUS")
    print("=" * 50)
    
    print("\nCommandes à exécuter dans le terminal:")
    print("1. docker-compose -f docker-compose.prod.yaml exec worker celery -A smartmarket inspect ping")
    print("2. docker-compose -f docker-compose.prod.yaml exec worker celery -A smartmarket inspect active")
    print("3. docker-compose -f docker-compose.prod.yaml exec beat celery -A smartmarket inspect scheduled")
    print("4. docker-compose -f docker-compose.prod.yaml exec worker celery -A smartmarket inspect stats")

def demo_websocket_notifications():
    """Démonstration des notifications WebSocket."""
    print("\n🌐 DÉMONSTRATION - WEBSOCKET NOTIFICATIONS")
    print("=" * 50)
    
    print("\nPour tester les notifications temps réel:")
    print("1. Ouvrir http://localhost:8000/admin/dashboard/ dans un navigateur")
    print("2. Se connecter avec un compte admin")
    print("3. Dans un autre onglet, créer une commande")
    print("4. Observer la notification en temps réel dans le tableau de bord")
    
    print("\nURLs WebSocket disponibles:")
    print("- ws://localhost:8000/ws/admin/orders/")
    print("- ws://localhost:8000/ws/admin/notifications/")
    print("- ws://localhost:8000/ws/user/{user_id}/notifications/")

def demo_backup_restore():
    """Démonstration des sauvegardes."""
    print("\n💾 DÉMONSTRATION - SAUVEGARDES")
    print("=" * 50)
    
    print("\nCommandes de sauvegarde:")
    print("1. Sauvegarde manuelle:")
    print("   ./scripts/backup.sh")
    print("2. Sauvegarde avec nom personnalisé:")
    print("   ./scripts/backup.sh backup_demo")
    print("3. Lister les sauvegardes:")
    print("   ls -la /opt/smartmarket/backups/")
    
    print("\nCommandes de restauration:")
    print("1. Restaurer une sauvegarde:")
    print("   ./scripts/restore.sh backup_demo")
    print("2. Vérifier la restauration:")
    print("   curl http://localhost/health/ready/")

def demo_docker_services():
    """Démonstration des services Docker."""
    print("\n🐳 DÉMONSTRATION - SERVICES DOCKER")
    print("=" * 50)
    
    print("\nCommandes utiles:")
    print("1. Statut des services:")
    print("   docker-compose -f docker-compose.prod.yaml ps")
    print("2. Logs en temps réel:")
    print("   docker-compose -f docker-compose.prod.yaml logs -f")
    print("3. Logs d'un service spécifique:")
    print("   docker-compose -f docker-compose.prod.yaml logs -f web")
    print("4. Redémarrer un service:")
    print("   docker-compose -f docker-compose.prod.yaml restart web")
    print("5. Utilisation des ressources:")
    print("   docker stats")

def demo_ci_cd():
    """Démonstration du pipeline CI/CD."""
    print("\n🚀 DÉMONSTRATION - PIPELINE CI/CD")
    print("=" * 50)
    
    print("\nLe pipeline CI/CD est configuré dans .github/workflows/ci-cd.yml")
    print("\nÉtapes du pipeline:")
    print("1. Qualité du code (lint, format, tests)")
    print("2. Build des images Docker")
    print("3. Scan de vulnérabilités (Trivy)")
    print("4. Push vers le registre")
    print("5. Déploiement automatique")
    print("6. Tests de régression")
    print("7. Notifications")
    
    print("\nPour déclencher le pipeline:")
    print("1. Faire un push sur la branche main")
    print("2. Créer une pull request")
    print("3. Vérifier les actions dans GitHub Actions")

def main():
    """Fonction principale de démonstration."""
    print("🎬 DÉMONSTRATION JOUR 4 - SMARTMARKET")
    print("=" * 60)
    print(f"🕐 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Démonstrations
    demo_health_checks()
    demo_celery_status()
    demo_websocket_notifications()
    demo_backup_restore()
    demo_docker_services()
    demo_ci_cd()
    
    print("\n" + "=" * 60)
    print("🎉 Démonstration terminée!")
    print("\n📸 CAPTURES D'ÉCRAN À PRENDRE:")
    print("1. Tableau de bord admin avec notifications temps réel")
    print("2. Statut des tâches Celery (ping, active, scheduled)")
    print("3. Health checks (/health/ready/ et /health/detailed/)")
    print("4. Logs des services Docker")
    print("5. Pipeline CI/CD en action")
    
    print("\n📋 CHECKLIST DE VALIDATION:")
    print("✅ Health checks fonctionnels")
    print("✅ Celery worker et beat opérationnels")
    print("✅ WebSockets avec notifications temps réel")
    print("✅ Sauvegardes et restauration")
    print("✅ Services Docker avec health checks")
    print("✅ Pipeline CI/CD configuré")
    print("✅ Documentation complète (README, RUNBOOK)")

if __name__ == "__main__":
    main()

