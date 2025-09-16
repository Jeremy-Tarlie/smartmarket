# SmartMarket - API REST E-commerce

Projet e-commerce Django avec API REST complète, authentification, RBAC, sécurité et conformité RGPD.

## 🚀 Fonctionnalités

- **API REST** complète avec Django REST Framework
- **Authentification** session et token
- **RBAC** (Role-Based Access Control) avec groupes
- **Sécurité** : CSRF, CORS, en-têtes de sécurité, throttling
- **Conformité RGPD** : export et suppression des données
- **Documentation** OpenAPI avec Swagger/Redoc
- **Tests** avec couverture ≥ 60%
- **Qualité** : linting, formatting, tests automatisés

## 📋 Prérequis

- Python 3.8+
- PostgreSQL 12+
- pip

## 🛠️ Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd smartmarket
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de la base de données**
```bash
# Créer la base de données PostgreSQL
createdb smartmarket

# Variables d'environnement (optionnel)
export DB_NAME=smartmarket
export DB_USER=smartuser
export DB_PASSWORD=smartpass
export DB_HOST=localhost
export DB_PORT=5432
```

5. **Migrations et données de test**
```bash
cd src
python manage.py migrate
python manage.py create_groups_users
python manage.py seed_demo
```

6. **Lancer le serveur**
```bash
python manage.py runserver
```

## 👥 Utilisateurs de test

| Rôle | Email | Mot de passe | Permissions |
|------|-------|--------------|-------------|
| Admin | admin@smartmarket.com | admin123 | Toutes |
| Manager | manager@smartmarket.com | manager123 | Gestion catalogue + commandes |
| Client | client1@example.com | client123 | Lecture catalogue + ses commandes |
| Client | client2@example.com | client123 | Lecture catalogue + ses commandes |

## 🔗 Endpoints API

### Base URL
```
http://localhost:8000/api/v1/
```

### Catégories
- `GET /categories/` - Liste des catégories (public)
- `GET /categories/{id}/` - Détail d'une catégorie (public)

### Produits
- `GET /products/` - Liste des produits (public)
- `GET /products/{id}/` - Détail d'un produit (public)
- `POST /products/` - Créer un produit (manager/admin)
- `PUT/PATCH /products/{id}/` - Modifier un produit (manager/admin)
- `DELETE /products/{id}/` - Supprimer un produit (manager/admin)

### Commandes
- `GET /orders/` - Liste des commandes (authentifié)
- `GET /orders/{id}/` - Détail d'une commande (authentifié)
- `POST /orders/` - Créer une commande (authentifié)
- `PUT/PATCH /orders/{id}/` - Modifier une commande (authentifié)

### Utilisateurs (RGPD)
- `GET /users/{id}/export-gdpr/` - Export des données (authentifié)
- `POST /users/{id}/delete-gdpr/` - Suppression des données (authentifié)

### Documentation
- `GET /api/docs/` - Interface Swagger
- `GET /api/redoc/` - Interface ReDoc
- `GET /api/schema/` - Schéma OpenAPI

## 🔐 Authentification

### Session (recommandé)
```bash
# Connexion via l'interface admin
curl -X POST http://localhost:8000/admin/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@smartmarket.com&password=admin123"
```

### Token (pour les clients API)
```bash
# Obtenir un token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@smartmarket.com", "password": "admin123"}'

# Utiliser le token
curl -H "Authorization: Token <your-token>" \
  http://localhost:8000/api/v1/orders/
```

## 📊 Exemples d'utilisation

### Créer une commande
```bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your-token>" \
  -d '{
    "shipping_address": "123 Rue de la Paix, 75001 Paris",
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ]
  }'
```

### Filtrer les produits
```bash
# Par catégorie
curl "http://localhost:8000/api/v1/products/?category=electronique"

# Par prix
curl "http://localhost:8000/api/v1/products/?min_price=100&max_price=500"

# Recherche
curl "http://localhost:8000/api/v1/products/?search=smartphone"
```

### Export RGPD
```bash
curl -H "Authorization: Token <your-token>" \
  http://localhost:8000/api/v1/users/1/export-gdpr/
```

## 🧪 Tests

### Lancer tous les tests
```bash
cd src
python -m pytest
```

### Tests avec couverture
```bash
python -m pytest --cov=. --cov-report=html
```

### Tests spécifiques
```bash
# Tests API uniquement
python -m pytest catalog/test_api.py

# Tests avec marqueurs
python -m pytest -m "not slow"
```

## 🔧 Qualité du code

### Formatage
```bash
black src/
ruff check src/ --fix
```

### Linting
```bash
ruff check src/
```

## 🚀 Déploiement

### Variables d'environnement de production
```bash
export DEBUG=False
export SECRET_KEY="your-secret-key"
export DB_NAME="smartmarket_prod"
export DB_USER="smartuser"
export DB_PASSWORD="secure-password"
export DB_HOST="your-db-host"
export ALLOWED_HOSTS="your-domain.com,www.your-domain.com"
```

### Lancer en production
```bash
python manage.py collectstatic
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## 📝 Rôles et permissions

### Admin
- Accès complet à toutes les fonctionnalités
- Gestion des utilisateurs
- Export/suppression RGPD de tous les utilisateurs

### Manager
- Gestion du catalogue (CRUD produits/catégories)
- Consultation de toutes les commandes
- Modification des statuts de commandes

### Client
- Consultation du catalogue
- Création et gestion de ses propres commandes
- Export/suppression de ses propres données RGPD

## 🔒 Sécurité

- **CSRF** : Protection contre les attaques CSRF
- **CORS** : Configuration stricte des origines autorisées
- **Throttling** : Limitation du débit par utilisateur
- **En-têtes de sécurité** : HSTS, X-Frame-Options, etc.
- **Validation** : Validation stricte des données d'entrée

## 📋 Conformité RGPD

- **Export des données** : JSON structuré avec toutes les données utilisateur
- **Suppression** : Suppression logique avec anonymisation
- **Journalisation** : Traces de toutes les opérations RGPD
- **Minimisation** : Seules les données nécessaires sont exposées

## 🐛 Dépannage

### Erreur de base de données
```bash
# Vérifier la connexion
python manage.py dbshell

# Réinitialiser les migrations
python manage.py migrate --fake-initial
```

### Erreur de permissions
```bash
# Recréer les groupes
python manage.py create_groups_users --reset
```

### Problème de CORS
Vérifier la configuration dans `settings/base.py` :
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## 📞 Support

Pour toute question ou problème :
1. Vérifier la documentation OpenAPI : `/api/docs/`
2. Consulter les logs : `tail -f /var/log/smartmarket/django.log`
3. Lancer les tests pour identifier les problèmes

## 📄 Licence

Ce projet est sous licence MIT.