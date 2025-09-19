#!/bin/bash

# Script de sauvegarde pour SmartMarket
# Usage: ./scripts/backup.sh [backup_name]

set -e

# Configuration
BACKUP_DIR="/opt/smartmarket/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME=${1:-"backup_$DATE"}
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Variables d'environnement
POSTGRES_DB=${POSTGRES_DB:-smartmarket}
POSTGRES_USER=${POSTGRES_USER:-smartmarket}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Créer le répertoire de sauvegarde
mkdir -p "$BACKUP_PATH"

echo "🚀 Début de la sauvegarde SmartMarket - $BACKUP_NAME"
echo "📁 Répertoire de sauvegarde: $BACKUP_PATH"

# 1. Sauvegarde de la base de données
echo "📊 Sauvegarde de la base de données..."
docker-compose -f docker-compose.prod.yaml exec -T db pg_dump \
    -U "$POSTGRES_USER" \
    -h localhost \
    -d "$POSTGRES_DB" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    > "$BACKUP_PATH/database.sql"

if [ $? -eq 0 ]; then
    echo "✅ Base de données sauvegardée avec succès"
else
    echo "❌ Erreur lors de la sauvegarde de la base de données"
    exit 1
fi

# 2. Sauvegarde des fichiers média
echo "📁 Sauvegarde des fichiers média..."
if [ -d "/opt/smartmarket/media" ]; then
    tar -czf "$BACKUP_PATH/media.tar.gz" -C /opt/smartmarket media/
    echo "✅ Fichiers média sauvegardés avec succès"
else
    echo "⚠️ Aucun fichier média à sauvegarder"
fi

# 3. Sauvegarde des fichiers statiques
echo "🎨 Sauvegarde des fichiers statiques..."
if [ -d "/opt/smartmarket/static" ]; then
    tar -czf "$BACKUP_PATH/static.tar.gz" -C /opt/smartmarket static/
    echo "✅ Fichiers statiques sauvegardés avec succès"
else
    echo "⚠️ Aucun fichier statique à sauvegarder"
fi

# 4. Sauvegarde des logs
echo "📝 Sauvegarde des logs..."
if [ -d "/opt/smartmarket/logs" ]; then
    tar -czf "$BACKUP_PATH/logs.tar.gz" -C /opt/smartmarket logs/
    echo "✅ Logs sauvegardés avec succès"
else
    echo "⚠️ Aucun log à sauvegarder"
fi

# 5. Sauvegarde de la configuration
echo "⚙️ Sauvegarde de la configuration..."
cp docker-compose.prod.yaml "$BACKUP_PATH/" 2>/dev/null || echo "⚠️ docker-compose.prod.yaml non trouvé"
cp .env "$BACKUP_PATH/" 2>/dev/null || echo "⚠️ .env non trouvé"
cp -r docker/ "$BACKUP_PATH/" 2>/dev/null || echo "⚠️ Répertoire docker non trouvé"

# 6. Sauvegarde des artefacts ML
echo "🤖 Sauvegarde des artefacts ML..."
if [ -d "/opt/smartmarket/src/var/ml" ]; then
    tar -czf "$BACKUP_PATH/ml_artifacts.tar.gz" -C /opt/smartmarket/src var/ml/
    echo "✅ Artefacts ML sauvegardés avec succès"
else
    echo "⚠️ Aucun artefact ML à sauvegarder"
fi

# 7. Créer un manifest de sauvegarde
echo "📋 Création du manifest de sauvegarde..."
cat > "$BACKUP_PATH/manifest.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "created_at": "$(date -Iseconds)",
    "version": "1.0.0",
    "components": {
        "database": "database.sql",
        "media": "media.tar.gz",
        "static": "static.tar.gz",
        "logs": "logs.tar.gz",
        "ml_artifacts": "ml_artifacts.tar.gz"
    },
    "environment": {
        "postgres_db": "$POSTGRES_DB",
        "postgres_user": "$POSTGRES_USER"
    },
    "size_bytes": $(du -sb "$BACKUP_PATH" | cut -f1)
}
EOF

# 8. Calculer la taille et créer un résumé
TOTAL_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
echo "📊 Taille totale de la sauvegarde: $TOTAL_SIZE"

# 9. Nettoyer les anciennes sauvegardes (garder les 7 dernières)
echo "🧹 Nettoyage des anciennes sauvegardes..."
cd "$BACKUP_DIR"
ls -t | tail -n +8 | xargs -r rm -rf
echo "✅ Nettoyage terminé"

# 10. Vérification de l'intégrité
echo "🔍 Vérification de l'intégrité..."
if [ -f "$BACKUP_PATH/database.sql" ] && [ -f "$BACKUP_PATH/manifest.json" ]; then
    echo "✅ Sauvegarde complète et intègre"
    echo "📁 Emplacement: $BACKUP_PATH"
    echo "📋 Manifest: $BACKUP_PATH/manifest.json"
else
    echo "❌ Erreur: Sauvegarde incomplète"
    exit 1
fi

echo "🎉 Sauvegarde terminée avec succès!"
echo "💾 Nom: $BACKUP_NAME"
echo "📅 Date: $(date)"
echo "📊 Taille: $TOTAL_SIZE"

