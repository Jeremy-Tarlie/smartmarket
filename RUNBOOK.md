# RUNBOOK - SmartMarket

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Procédures de démarrage](#procédures-de-démarrage)
4. [Procédures d'arrêt](#procédures-darrêt)
5. [Migrations](#migrations)
6. [Sauvegardes](#sauvegardes)
7. [Restauration](#restauration)
8. [Rollback](#rollback)
9. [Monitoring](#monitoring)
10. [Dépannage](#dépannage)
11. [Contacts d'urgence](#contacts-durgence)

## Vue d'ensemble

SmartMarket est une application e-commerce Django avec des fonctionnalités ML, des tâches asynchrones (Celery) et des notifications temps réel (WebSockets).

### Composants principaux

- **Web** : Application Django avec Gunicorn
- **Worker** : Celery worker pour les tâches asynchrones
- **Beat** : Celery beat pour la planification
- **Nginx** : Reverse proxy et serveur de fichiers statiques
- **PostgreSQL** : Base de données principale
- **Redis** : Cache et broker pour Celery/Channels

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Nginx    │────│     Web     │────│ PostgreSQL  │
│  (Port 80)  │    │ (Port 8000) │    │ (Port 5432) │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Worker    │────│    Beat     │────│    Redis    │
│  (Celery)   │    │ (Celery)    │    │ (Port 6379) │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Procédures de démarrage

### Démarrage en production

```bash
# 1. Se connecter au serveur
ssh user@production-server

# 2. Aller dans le répertoire de l'application
cd /opt/smartmarket

# 3. Vérifier les variables d'environnement
cat .env

# 4. Démarrer tous les services
docker-compose -f docker-compose.prod.yaml up -d

# 5. Vérifier le statut des services
docker-compose -f docker-compose.prod.yaml ps

# 6. Vérifier les logs
docker-compose -f docker-compose.prod.yaml logs -f
```

### Démarrage en développement

```bash
# 1. Cloner le repository
git clone <repository-url>
cd smartmarket

# 2. Copier les variables d'environnement
cp env.example .env

# 3. Démarrer les services de développement
docker-compose -f docker-compose.dev.yaml up -d

# 4. Appliquer les migrations
docker-compose -f docker-compose.dev.yaml exec web python manage.py migrate

# 5. Créer un superutilisateur
docker-compose -f docker-compose.dev.yaml exec web python manage.py createsuperuser

# 6. Construire les index ML
docker-compose -f docker-compose.dev.yaml exec web python manage.py build_ml_indexes
docker-compose -f docker-compose.dev.yaml exec web python manage.py build_rag_index
```

## Procédures d'arrêt

### Arrêt gracieux

```bash
# 1. Arrêter tous les services
docker-compose -f docker-compose.prod.yaml down

# 2. Vérifier qu'aucun conteneur ne tourne
docker ps

# 3. Nettoyer les conteneurs arrêtés (optionnel)
docker container prune -f
```

### Arrêt d'urgence

```bash
# 1. Arrêter immédiatement tous les conteneurs
docker-compose -f docker-compose.prod.yaml kill

# 2. Supprimer les conteneurs
docker-compose -f docker-compose.prod.yaml rm -f
```

## Migrations

### Migrations de base de données

```bash
# 1. Créer une sauvegarde avant migration
./scripts/backup.sh "pre_migration_$(date +%Y%m%d_%H%M%S)"

# 2. Appliquer les migrations
docker-compose -f docker-compose.prod.yaml exec web python manage.py migrate

# 3. Vérifier le statut des migrations
docker-compose -f docker-compose.prod.yaml exec web python manage.py showmigrations

# 4. Collecter les fichiers statiques
docker-compose -f docker-compose.prod.yaml exec web python manage.py collectstatic --noinput
```

### Migrations de données

```bash
# 1. Créer une migration personnalisée
docker-compose -f docker-compose.prod.yaml exec web python manage.py makemigrations

# 2. Tester la migration en développement
docker-compose -f docker-compose.dev.yaml exec web python manage.py migrate

# 3. Appliquer en production après validation
docker-compose -f docker-compose.prod.yaml exec web python manage.py migrate
```

## Sauvegardes

### Sauvegarde automatique

Les sauvegardes sont planifiées via Celery Beat :

```bash
# Vérifier les tâches planifiées
docker-compose -f docker-compose.prod.yaml exec beat celery -A smartmarket inspect scheduled
```

### Sauvegarde manuelle

```bash
# 1. Sauvegarde complète
./scripts/backup.sh

# 2. Sauvegarde avec nom personnalisé
./scripts/backup.sh "backup_avant_maintenance"

# 3. Lister les sauvegardes disponibles
ls -la /opt/smartmarket/backups/

# 4. Vérifier une sauvegarde
cat /opt/smartmarket/backups/backup_YYYYMMDD_HHMMSS/manifest.json
```

### Sauvegarde de la base de données uniquement

```bash
# Sauvegarde rapide de la DB
docker-compose -f docker-compose.prod.yaml exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_db_$(date +%Y%m%d_%H%M%S).sql
```

## Restauration

### Restauration complète

```bash
# 1. Lister les sauvegardes disponibles
ls -la /opt/smartmarket/backups/

# 2. Restaurer une sauvegarde
./scripts/restore.sh backup_YYYYMMDD_HHMMSS

# 3. Vérifier la restauration
curl -f http://localhost/health/ready/
```

### Restauration de la base de données uniquement

```bash
# 1. Arrêter l'application
docker-compose -f docker-compose.prod.yaml stop web worker beat

# 2. Restaurer la base de données
docker-compose -f docker-compose.prod.yaml exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB < backup_db_YYYYMMDD_HHMMSS.sql

# 3. Redémarrer l'application
docker-compose -f docker-compose.prod.yaml start web worker beat
```

## Rollback

### Rollback de déploiement

```bash
# 1. Identifier la version précédente
docker images | grep smartmarket

# 2. Mettre à jour docker-compose.prod.yaml avec l'ancienne version
sed -i 's|image: .*web.*|image: ghcr.io/username/smartmarket-web:previous-tag|g' docker-compose.prod.yaml

# 3. Redémarrer les services
docker-compose -f docker-compose.prod.yaml up -d

# 4. Vérifier le rollback
curl -f http://localhost/health/ready/
```

### Rollback de base de données

```bash
# 1. Restaurer la sauvegarde précédente
./scripts/restore.sh backup_previous_version

# 2. Vérifier l'intégrité
docker-compose -f docker-compose.prod.yaml exec web python manage.py check
```

## Monitoring

### Health checks

```bash
# 1. Vérification simple
curl http://localhost/health/live/

# 2. Vérification complète
curl http://localhost/health/ready/

# 3. Vérification détaillée
curl http://localhost/health/detailed/
```

### Monitoring des services

```bash
# 1. Statut des conteneurs
docker-compose -f docker-compose.prod.yaml ps

# 2. Logs en temps réel
docker-compose -f docker-compose.prod.yaml logs -f

# 3. Logs d'un service spécifique
docker-compose -f docker-compose.prod.yaml logs -f web

# 4. Utilisation des ressources
docker stats
```

### Monitoring Celery

```bash
# 1. Statut des workers
docker-compose -f docker-compose.prod.yaml exec worker celery -A smartmarket inspect active

# 2. Tâches planifiées
docker-compose -f docker-compose.prod.yaml exec beat celery -A smartmarket inspect scheduled

# 3. Statistiques des workers
docker-compose -f docker-compose.prod.yaml exec worker celery -A smartmarket inspect stats
```

### Monitoring Redis

```bash
# 1. Connexion à Redis
docker-compose -f docker-compose.prod.yaml exec redis redis-cli

# 2. Informations sur Redis
docker-compose -f docker-compose.prod.yaml exec redis redis-cli info

# 3. Taille de la base de données
docker-compose -f docker-compose.prod.yaml exec redis redis-cli dbsize
```

## Dépannage

### Problèmes courants

#### Service web ne démarre pas

```bash
# 1. Vérifier les logs
docker-compose -f docker-compose.prod.yaml logs web

# 2. Vérifier la configuration
docker-compose -f docker-compose.prod.yaml config

# 3. Tester la connexion à la base de données
docker-compose -f docker-compose.prod.yaml exec web python manage.py dbshell
```

#### Worker Celery ne traite pas les tâches

```bash
# 1. Vérifier les logs du worker
docker-compose -f docker-compose.prod.yaml logs worker

# 2. Vérifier la connexion Redis
docker-compose -f docker-compose.prod.yaml exec worker celery -A smartmarket inspect ping

# 3. Redémarrer le worker
docker-compose -f docker-compose.prod.yaml restart worker
```

#### Problèmes de WebSocket

```bash
# 1. Vérifier la configuration Nginx
docker-compose -f docker-compose.prod.yaml exec nginx nginx -t

# 2. Vérifier les logs Channels
docker-compose -f docker-compose.prod.yaml logs web | grep -i websocket

# 3. Tester la connexion WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://localhost/ws/admin/orders/
```

#### Problèmes de performance

```bash
# 1. Vérifier l'utilisation des ressources
docker stats

# 2. Vérifier les logs d'erreur
docker-compose -f docker-compose.prod.yaml logs | grep -i error

# 3. Vérifier la taille de la base de données
docker-compose -f docker-compose.prod.yaml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));"
```

### Commandes de diagnostic

```bash
# 1. Vérification complète du système
docker-compose -f docker-compose.prod.yaml exec web python manage.py check --deploy

# 2. Test de la base de données
docker-compose -f docker-compose.prod.yaml exec web python manage.py dbshell

# 3. Test des tâches Celery
docker-compose -f docker-compose.prod.yaml exec web python manage.py shell -c "from catalog.tasks import debug_task; debug_task.delay()"

# 4. Test des WebSockets
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://localhost/ws/admin/orders/
```

## Contacts d'urgence

### Équipe technique

- **Lead Developer** : [Nom] - [Email] - [Téléphone]
- **DevOps** : [Nom] - [Email] - [Téléphone]
- **DBA** : [Nom] - [Email] - [Téléphone]

### Escalade

1. **Niveau 1** : Équipe technique (0-30 min)
2. **Niveau 2** : Lead Developer (30-60 min)
3. **Niveau 3** : CTO (1-2 heures)

### Procédure d'urgence

En cas d'incident critique :

1. **Évaluer l'impact** : Service down, données corrompues, sécurité compromise
2. **Communiquer** : Notifier l'équipe via Slack/Email
3. **Isoler** : Arrêter les services si nécessaire
4. **Diagnostiquer** : Utiliser les commandes de diagnostic
5. **Résoudre** : Appliquer la solution ou le rollback
6. **Documenter** : Enregistrer l'incident et la résolution

### Numéros d'urgence

- **Incident critique** : [Numéro]
- **Support 24/7** : [Numéro]
- **Escalade management** : [Numéro]

---

**Dernière mise à jour** : [Date]
**Version** : 1.0.0
**Responsable** : [Nom]

