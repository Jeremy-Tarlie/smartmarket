#!/bin/bash

# Script de démarrage rapide pour SmartMarket Jour 4
# Usage: ./scripts/quick_start.sh [dev|prod]

set -e

MODE=${1:-dev}

echo "🚀 Démarrage rapide SmartMarket - Mode: $MODE"
echo "=" * 50

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp env.example .env
    echo "⚠️ Veuillez éditer le fichier .env avec vos valeurs avant de continuer."
    echo "   Appuyez sur Entrée quand c'est fait..."
    read
fi

if [ "$MODE" = "prod" ]; then
    echo "🏭 Mode production"
    
    # Démarrer les services de production
    echo "🐳 Démarrage des services Docker..."
    docker-compose -f docker-compose.prod.yaml up -d
    
    # Attendre que les services soient prêts
    echo "⏳ Attente du démarrage des services..."
    sleep 30
    
    # Appliquer les migrations
    echo "📊 Application des migrations..."
    docker-compose -f docker-compose.prod.yaml exec web python manage.py migrate
    
    # Créer un superutilisateur
    echo "👤 Création d'un superutilisateur..."
    docker-compose -f docker-compose.prod.yaml exec web python manage.py createsuperuser --noinput --username admin --email admin@smartmarket.com || true
    
    # Construire les index ML
    echo "🤖 Construction des index ML..."
    docker-compose -f docker-compose.prod.yaml exec web python manage.py build_ml_indexes || echo "⚠️ Index ML non construits (normal en première installation)"
    docker-compose -f docker-compose.prod.yaml exec web python manage.py build_rag_index || echo "⚠️ Index RAG non construit (normal en première installation)"
    
    # Collecter les fichiers statiques
    echo "🎨 Collection des fichiers statiques..."
    docker-compose -f docker-compose.prod.yaml exec web python manage.py collectstatic --noinput
    
    echo "✅ Services de production démarrés!"
    echo "🌐 Application disponible sur: http://localhost"
    echo "📊 Tableau de bord admin: http://localhost/admin/dashboard/"
    
else
    echo "🛠️ Mode développement"
    
    # Démarrer les services de développement
    echo "🐳 Démarrage des services Docker..."
    docker-compose -f docker-compose.dev.yaml up -d
    
    # Attendre que les services soient prêts
    echo "⏳ Attente du démarrage des services..."
    sleep 20
    
    # Appliquer les migrations
    echo "📊 Application des migrations..."
    docker-compose -f docker-compose.dev.yaml exec web python manage.py migrate
    
    # Créer un superutilisateur
    echo "👤 Création d'un superutilisateur..."
    docker-compose -f docker-compose.dev.yaml exec web python manage.py createsuperuser --noinput --username admin --email admin@smartmarket.com || true
    
    # Construire les index ML
    echo "🤖 Construction des index ML..."
    docker-compose -f docker-compose.dev.yaml exec web python manage.py build_ml_indexes || echo "⚠️ Index ML non construits (normal en première installation)"
    docker-compose -f docker-compose.dev.yaml exec web python manage.py build_rag_index || echo "⚠️ Index RAG non construit (normal en première installation)"
    
    echo "✅ Services de développement démarrés!"
    echo "🌐 Application disponible sur: http://localhost:8000"
    echo "📊 Tableau de bord admin: http://localhost:8000/admin/dashboard/"
fi

# Vérifier la santé des services
echo "🔍 Vérification de la santé des services..."
sleep 10

if [ "$MODE" = "prod" ]; then
    HEALTH_URL="http://localhost/health/ready/"
else
    HEALTH_URL="http://localhost:8000/health/ready/"
fi

if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Services opérationnels!"
else
    echo "⚠️ Services en cours de démarrage..."
    echo "   Vérifiez les logs: docker-compose logs -f"
fi

echo ""
echo "🎉 SmartMarket est prêt!"
echo ""
echo "📋 Commandes utiles:"
echo "   - Voir les logs: docker-compose -f docker-compose.$MODE.yaml logs -f"
echo "   - Arrêter: docker-compose -f docker-compose.$MODE.yaml down"
echo "   - Redémarrer: docker-compose -f docker-compose.$MODE.yaml restart"
echo ""
echo "🧪 Tests:"
echo "   - Health checks: curl $HEALTH_URL"
echo "   - Test complet: python scripts/test_jour4.py"
echo "   - Démonstration: python scripts/demo_jour4.py"
echo ""
echo "📚 Documentation:"
echo "   - README: README_JOUR4.md"
echo "   - Runbook: RUNBOOK.md"
echo "   - API: http://localhost:8000/api/v1/"

