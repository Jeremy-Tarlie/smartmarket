"""
Configuration pour le module ML.
"""

import os
from pathlib import Path

# Chemins des artefacts ML
BASE_DIR = Path(__file__).resolve().parent.parent
ML_ARTIFACTS_DIR = BASE_DIR / "var" / "ml"
ML_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration des modèles
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Configuration des index
FAISS_INDEX_PATH = ML_ARTIFACTS_DIR / "faiss_index.bin"
TFIDF_MODEL_PATH = ML_ARTIFACTS_DIR / "tfidf_model.pkl"
PRODUCT_EMBEDDINGS_PATH = ML_ARTIFACTS_DIR / "product_embeddings.npy"
RAG_INDEX_PATH = ML_ARTIFACTS_DIR / "rag_index.bin"

# Configuration des recommandations
DEFAULT_RECOMMENDATIONS_K = 10
MAX_RECOMMENDATIONS_K = 50

# Configuration de la recherche
DEFAULT_SEARCH_K = 20
MAX_SEARCH_K = 100

# Configuration RAG
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 5

# Configuration du cache
CACHE_TTL = 3600  # 1 heure
CACHE_PREFIX = "smartmarket_ml"

# Configuration des performances
RECOMMENDATION_TIMEOUT = 0.15  # 150ms
SEARCH_TIMEOUT = 0.3  # 300ms
RAG_TIMEOUT = 2.0  # 2s

# Configuration OpenAI (pour RAG)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_MAX_TOKENS = 500

