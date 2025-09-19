#!/bin/bash

# Script de restauration pour SmartMarket
# Usage: ./scripts/restore.sh <backup_name>

set -e

# Vérification des arguments
if [ $# -eq 0 ]; then
    echo "❌ Usage: $0 <backup_name>"
    echo "📋 Sauvegardes disponibles:"
    ls -la /opt/smartmarket/backups/ 2>/dev/null || echo "Aucune sauvegarde trouvée"
    exit 1
fi

BACKUP_NAME=$1
BACKUP_DIR="/opt/smartmarket/backups"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Variables d'environnement
POSTGRES_DB=${POSTGRES_DB:-smartmarket}
POSTGRES_USER=${POSTGRES_USER:-smartmarket}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Vérifier que la sauvegarde existe
if [ ! -d "$BACKUP_PATH" ]; then
    echo "❌ Sauvegarde non trouvée: $BACKUP_PATH"
    echo "📋 Sauvegardes disponibles:"
    ls -la "$BACKUP_DIR/" 2>/dev/null || echo "Aucune sauvegarde trouvée"
    exit 1
fi

# Vérifier le manifest
if [ ! -f "$BACKUP_PATH/manifest.json" ]; then
    echo "❌ Manifest de sauvegarde non trouvé: $BACKUP_PATH/manifest.json"
    exit 1
fi

echo "🚀 Début de la restauration SmartMarket - $BACKUP_NAME"
echo "📁 Répertoire de sauvegarde: $BACKUP_PATH"

# Afficher les informations de la sauvegarde
echo "📋 Informations de la sauvegarde:"
cat "$BACKUP_PATH/manifest.json" | jq '.' 2>/dev/null || cat "$BACKUP_PATH/manifest.json"

# Confirmation
read -p "⚠️ Cette opération va remplacer les données actuelles. Continuer? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restauration annulée"
    exit 1
fi

# 1. Arrêter les services
echo "🛑 Arrêt des services..."
docker-compose -f docker-compose.prod.yaml down

# 2. Sauvegarde de sécurité de l'état actuel
echo "💾 Création d'une sauvegarde de sécurité..."
SAFETY_BACKUP="safety_backup_$(date +%Y%m%d_%H%M%S)"
./scripts/backup.sh "$SAFETY_BACKUP"
echo "✅ Sauvegarde de sécurité créée: $SAFETY_BACKUP"

# 3. Restauration de la base de données
echo "📊 Restauration de la base de données..."
if [ -f "$BACKUP_PATH/database.sql" ]; then
    # Démarrer seulement la base de données
    docker-compose -f docker-compose.prod.yaml up -d db
    sleep 10
    
    # Attendre que PostgreSQL soit prêt
    echo "⏳ Attente de PostgreSQL..."
    until docker-compose -f docker-compose.prod.yaml exec db pg_isready -U "$POSTGRES_USER"; do
        echo "En attente de PostgreSQL..."
        sleep 2
    done
    
    # Restaurer la base de données
    docker-compose -f docker-compose.prod.yaml exec -T db psql \
        -U "$POSTGRES_USER" \
        -d postgres \
        < "$BACKUP_PATH/database.sql"
    
    if [ $? -eq 0 ]; then
        echo "✅ Base de données restaurée avec succès"
    else
        echo "❌ Erreur lors de la restauration de la base de données"
        echo "🔄 Restauration de la sauvegarde de sécurité..."
        ./scripts/restore.sh "$SAFETY_BACKUP"
        exit 1
    fi
else
    echo "❌ Fichier de base de données non trouvé: $BACKUP_PATH/database.sql"
    exit 1
fi

# 4. Restauration des fichiers média
echo "📁 Restauration des fichiers média..."
if [ -f "$BACKUP_PATH/media.tar.gz" ]; then
    # Supprimer les anciens fichiers média
    rm -rf /opt/smartmarket/media
    mkdir -p /opt/smartmarket/media
    
    # Extraire les fichiers média
    tar -xzf "$BACKUP_PATH/media.tar.gz" -C /opt/smartmarket/
    echo "✅ Fichiers média restaurés avec succès"
else
    echo "⚠️ Aucun fichier média à restaurer"
fi

# 5. Restauration des fichiers statiques
echo "🎨 Restauration des fichiers statiques..."
if [ -f "$BACKUP_PATH/static.tar.gz" ]; then
    # Supprimer les anciens fichiers statiques
    rm -rf /opt/smartmarket/static
    mkdir -p /opt/smartmarket/static
    
    # Extraire les fichiers statiques
    tar -xzf "$BACKUP_PATH/static.tar.gz" -C /opt/smartmarket/
    echo "✅ Fichiers statiques restaurés avec succès"
else
    echo "⚠️ Aucun fichier statique à restaurer"
fi

# 6. Restauration des artefacts ML
echo "🤖 Restauration des artefacts ML..."
if [ -f "$BACKUP_PATH/ml_artifacts.tar.gz" ]; then
    # Supprimer les anciens artefacts ML
    rm -rf /opt/smartmarket/src/var/ml
    mkdir -p /opt/smartmarket/src/var
    
    # Extraire les artefacts ML
    tar -xzf "$BACKUP_PATH/ml_artifacts.tar.gz" -C /opt/smartmarket/src/
    echo "✅ Artefacts ML restaurés avec succès"
else
    echo "⚠️ Aucun artefact ML à restaurer"
fi

# 7. Redémarrer tous les services
echo "🚀 Redémarrage des services..."
docker-compose -f docker-compose.prod.yaml up -d

# 8. Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 30

# 9. Vérification de la santé des services
echo "🔍 Vérification de la santé des services..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost/health/ready/ > /dev/null 2>&1; then
        echo "✅ Services opérationnels"
        break
    else
        echo "⏳ Attente des services... ($((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Les services ne répondent pas après $MAX_RETRIES tentatives"
    echo "🔄 Restauration de la sauvegarde de sécurité..."
    ./scripts/restore.sh "$SAFETY_BACKUP"
    exit 1
fi

# 10. Tests de régression
echo "🧪 Tests de régression..."
if curl -f http://localhost/health/live/ > /dev/null 2>&1; then
    echo "✅ Health check live: OK"
else
    echo "❌ Health check live: ÉCHEC"
fi

if curl -f http://localhost/health/ready/ > /dev/null 2>&1; then
    echo "✅ Health check ready: OK"
else
    echo "❌ Health check ready: ÉCHEC"
fi

# 11. Nettoyage de la sauvegarde de sécurité (optionnel)
read -p "🗑️ Supprimer la sauvegarde de sécurité? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$BACKUP_DIR/$SAFETY_BACKUP"
    echo "✅ Sauvegarde de sécurité supprimée"
else
    echo "💾 Sauvegarde de sécurité conservée: $SAFETY_BACKUP"
fi

echo "🎉 Restauration terminée avec succès!"
echo "📅 Date: $(date)"
echo "📊 Sauvegarde restaurée: $BACKUP_NAME"
echo "🌐 Application disponible sur: http://localhost"

