# SmartMarket - Module ML (Jour 3)

## Vue d'ensemble

Ce module implémente les fonctionnalités d'intelligence artificielle pour SmartMarket :
- **Recommandations basées contenu** avec similarité sémantique
- **Recherche sémantique** avec index vectoriel FAISS
- **Assistant RAG** (Retrieval-Augmented Generation) pour l'aide à l'achat
- **Cache Redis** pour optimiser les performances
- **Traçabilité** et versioning des artefacts ML

## Prérequis

### Dépendances Python
```bash
pip install -r requirements.txt
```

### Services externes
- **Redis** : Cache pour optimiser les performances
- **OpenAI API** (optionnel) : Pour l'assistant RAG avec LLM

### Variables d'environnement
```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenAI (optionnel pour RAG)
OPENAI_API_KEY=your_openai_api_key
```

## Installation et configuration

### 1. Installation des dépendances
```bash
cd src
pip install -r requirements.txt
```

### 2. Configuration Redis
```bash
# Installation Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Démarrage Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérification
redis-cli ping
```

### 3. Configuration Django
Les paramètres ML sont configurés dans `smartmarket/settings/base.py` :
- Configuration Redis
- Throttling des endpoints ML
- Paramètres de performance

## Construction des index ML

### 1. Index de recommandations et recherche
```bash
cd src
python manage.py build_ml_indexes
```

Cette commande :
- Entraîne le modèle TF-IDF sur les produits
- Génère les embeddings sémantiques avec SentenceTransformers
- Construit l'index FAISS pour la recherche
- Enregistre les artefacts dans le manifest

### 2. Index RAG pour l'assistant
```bash
cd src
python manage.py build_rag_index
```

Cette commande :
- Crée des documents de démonstration (FAQ, politiques, guides)
- Découpe les documents en chunks
- Génère les embeddings et construit l'index RAG
- Enregistre l'index dans le manifest

### 3. Vérification des index
```bash
cd src
python manage.py shell
>>> from ml.manifest import ml_manifest
>>> print(ml_manifest.get_manifest_summary())
```

## Endpoints API

### Recommandations
```http
GET /api/v1/products/{id}/recommendations/?k=10&diversity=true
```

**Paramètres :**
- `k` : Nombre de recommandations (max 50)
- `diversity` : Utiliser MMR pour la diversité (true/false)

**Réponse :**
```json
{
  "product_id": 123,
  "product_name": "Smartphone Samsung",
  "recommendations": [
    {
      "id": 124,
      "name": "iPhone 15",
      "price": "999.99",
      "similarity_score": 0.85,
      "reason": "Similaire par catégorie et caractéristiques"
    }
  ],
  "count": 1,
  "response_time_ms": 45.2,
  "status": "success"
}
```

### Recherche sémantique
```http
GET /api/v1/search?q=smartphone&k=20&category=1&min_price=100&max_price=1000
```

**Paramètres :**
- `q` : Requête de recherche (obligatoire)
- `k` : Nombre de résultats (max 100)
- `category` : IDs des catégories (séparés par virgule)
- `min_price` : Prix minimum
- `max_price` : Prix maximum

**Réponse :**
```json
{
  "query": "smartphone",
  "results": [
    {
      "id": 123,
      "name": "Smartphone Samsung",
      "price": "699.99",
      "search_score": 0.92,
      "reason": "Correspondance excellente avec 'smartphone'"
    }
  ],
  "count": 1,
  "response_time_ms": 78.5,
  "status": "success"
}
```

### Assistant RAG
```http
POST /api/v1/assistant/ask
Content-Type: application/json

{
  "question": "Quelle est votre politique de retour ?",
  "user_context": {
    "user_id": 123,
    "preferences": ["electronics"]
  }
}
```

**Réponse :**
```json
{
  "answer": "Vous avez 30 jours pour retourner un produit non alimentaire en parfait état...",
  "sources": [
    {
      "content": "Vous avez 30 jours pour retourner un produit...",
      "metadata": {
        "type": "policy",
        "category": "returns",
        "title": "Politique de retour"
      },
      "score": 0.95
    }
  ],
  "trace_id": "abc123-def456",
  "confidence": 0.95,
  "status": "success",
  "response_time_ms": 1250.3
}
```

### Statut ML
```http
GET /api/v1/ml/status/
```

**Réponse :**
```json
{
  "cache": {
    "status": "connected",
    "total_keys": 150,
    "ml_keys": 45,
    "memory_usage": "2.1M"
  },
  "manifest": {
    "version": "1.0.0",
    "total_artifacts": 3,
    "total_models": 2,
    "total_indexes": 2
  },
  "services": {
    "recommendations": true,
    "search": true,
    "rag": true
  }
}
```

## Tests

### Tests unitaires
```bash
cd src
python manage.py test catalog.test_ml
```

### Tests de pertinence
```bash
cd src
python manage.py test catalog.test_ml.MLAPITestCase
```

### Jeu de tests de pertinence
Le fichier `test_data/relevance_test_cases.json` contient des cas de test pour évaluer :
- Précision des recommandations
- Pertinence de la recherche sémantique
- Qualité des réponses RAG

## Performance et budgets de latence

### Objectifs de performance
- **Recommandations** : P95 ≤ 150ms
- **Recherche sémantique** : P95 ≤ 300ms
- **Assistant RAG** : ≤ 2s

### Optimisations
- **Cache Redis** : TTL de 1 heure pour les résultats
- **Index FAISS** : Recherche approximative pour la vitesse
- **Throttling** : 30 requêtes/minute pour les endpoints ML
- **Invalidation automatique** : Cache vidé lors des modifications de produits

## Monitoring et métriques

### Métriques en ligne
- Temps de réponse (P95, P99)
- Taux de cache hit
- Volume de requêtes
- Taux d'erreur

### Métriques de qualité
- Précision@K pour les recommandations
- MRR et NDCG pour la recherche
- Taux de réponse pertinente pour RAG

## Sécurité et conformité

### RGPD
- Aucune donnée personnelle dans les index vectoriels
- Traçabilité des requêtes avec trace_id
- Possibilité d'effacement des historiques

### Sécurité
- Throttling des endpoints ML
- Validation des paramètres d'entrée
- Gestion des erreurs sans exposition d'informations sensibles

## Maintenance

### Réindexation
```bash
# Réindexation complète
python manage.py build_ml_indexes --force

# Réindexation RAG
python manage.py build_rag_index --force
```

### Nettoyage du cache
```bash
python manage.py shell
>>> from ml.cache import ml_cache
>>> ml_cache.invalidate_all_cache()
```

### Validation des artefacts
```bash
python manage.py shell
>>> from ml.manifest import ml_manifest
>>> print(ml_manifest.validate_artifacts())
```

## Limitations et améliorations futures

### Limitations actuelles
- Corpus de démonstration limité
- Pas de personnalisation utilisateur
- Assistant RAG basique sans fine-tuning

### Améliorations prévues
- Recommandations collaboratives
- A/B testing des algorithmes
- Métriques de business (CTR, conversion)
- Intégration avec des LLM plus avancés

## Support et dépannage

### Problèmes courants

**Index non trouvé :**
```bash
python manage.py build_ml_indexes
```

**Cache Redis indisponible :**
- Vérifier que Redis est démarré
- Vérifier la configuration dans settings.py

**Assistant RAG ne répond pas :**
- Vérifier la clé API OpenAI
- Construire l'index RAG : `python manage.py build_rag_index`

**Performances dégradées :**
- Vérifier l'état du cache Redis
- Réindexer les artefacts ML
- Vérifier les logs Django

### Logs
Les logs ML sont intégrés dans les logs Django standard. Niveau INFO pour les opérations normales, ERROR pour les problèmes.

## Contact

Pour toute question sur le module ML :
- Documentation technique : Ce README
- Tests : `catalog/test_ml.py`
- Manifest : `ml/manifest.py`

