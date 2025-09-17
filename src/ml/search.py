"""
Recherche sémantique avec index vectoriel FAISS.
"""

import pickle
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import faiss

from .config import (
    FAISS_INDEX_PATH,
    DEFAULT_SEARCH_K,
    MAX_SEARCH_K,
    EMBEDDING_DIMENSION,
)
from .preprocessing import preprocess_text


class SemanticSearchEngine:
    """Moteur de recherche sémantique avec FAISS."""
    
    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.product_ids: List[int] = []
        self.id_to_index: Dict[int, int] = {}
        self.embedding_model = None
    
    def load_embedding_model(self, embedding_model):
        """
        Charge le modèle d'embeddings.
        
        Args:
            embedding_model: Modèle SentenceTransformer
        """
        self.embedding_model = embedding_model
    
    def build_index(self, embeddings: np.ndarray, product_ids: List[int]):
        """
        Construit l'index FAISS.
        
        Args:
            embeddings: Matrice des embeddings
            product_ids: Liste des IDs des produits
        """
        if embeddings.shape[1] != EMBEDDING_DIMENSION:
            raise ValueError(f"Dimension d'embedding incorrecte: {embeddings.shape[1]} != {EMBEDDING_DIMENSION}")
        
        # Créer l'index FAISS
        self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)  # Inner Product (cosine similarity)
        
        # Normaliser les embeddings pour la similarité cosinus
        faiss.normalize_L2(embeddings)
        
        # Ajouter les embeddings à l'index
        self.index.add(embeddings.astype('float32'))
        
        # Sauvegarder les métadonnées
        self.product_ids = product_ids
        self.id_to_index = {pid: idx for idx, pid in enumerate(product_ids)}
        
        # Sauvegarder l'index
        self.save_index()
    
    def load_index(self):
        """Charge l'index FAISS sauvegardé."""
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError("Index FAISS non trouvé")
        
        # Charger l'index
        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        
        # Charger les métadonnées
        metadata_path = FAISS_INDEX_PATH.with_suffix('.metadata.pkl')
        if metadata_path.exists():
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                self.product_ids = metadata['product_ids']
                self.id_to_index = metadata['id_to_index']
        else:
            self.product_ids = []
            self.id_to_index = {}
    
    def save_index(self):
        """Sauvegarde l'index FAISS et ses métadonnées."""
        if self.index is None:
            raise ValueError("Index non construit")
        
        # Sauvegarder l'index
        faiss.write_index(self.index, str(FAISS_INDEX_PATH))
        
        # Sauvegarder les métadonnées
        metadata = {
            'product_ids': self.product_ids,
            'id_to_index': self.id_to_index,
        }
        metadata_path = FAISS_INDEX_PATH.with_suffix('.metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
    
    def search(
        self,
        query: str,
        k: int = DEFAULT_SEARCH_K,
        min_score: float = 0.1
    ) -> List[Tuple[int, float, str]]:
        """
        Effectue une recherche sémantique.
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats à retourner
            min_score: Score minimal requis
            
        Returns:
            Liste de tuples (product_id, score, reason)
        """
        if self.index is None or self.embedding_model is None:
            raise ValueError("Index ou modèle d'embeddings non chargé")
        
        # Limiter k
        k = min(k, MAX_SEARCH_K, len(self.product_ids))
        
        # Prétraiter la requête
        processed_query = preprocess_text(query, stem=False)
        
        # Générer l'embedding de la requête
        query_embedding = self.embedding_model.encode([processed_query])
        faiss.normalize_L2(query_embedding)
        
        # Rechercher dans l'index
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Formater les résultats
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Index invalide
                continue
            
            if score >= min_score:
                product_id = self.product_ids[idx]
                reason = self._generate_search_reason(query, score)
                results.append((product_id, float(score), reason))
        
        return results
    
    def _generate_search_reason(self, query: str, score: float) -> str:
        """
        Génère une raison pour le résultat de recherche.
        
        Args:
            query: Requête originale
            score: Score de similarité
            
        Returns:
            Raison du résultat
        """
        if score > 0.8:
            return f"Correspondance excellente avec '{query}'"
        elif score > 0.6:
            return f"Correspondance forte avec '{query}'"
        elif score > 0.4:
            return f"Correspondance modérée avec '{query}'"
        else:
            return f"Correspondance faible avec '{query}'"
    
    def search_with_filters(
        self,
        query: str,
        k: int = DEFAULT_SEARCH_K,
        category_ids: Optional[List[int]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        active_only: bool = True
    ) -> List[Tuple[int, float, str]]:
        """
        Effectue une recherche avec filtres.
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats à retourner
            category_ids: IDs des catégories à inclure
            min_price: Prix minimum
            max_price: Prix maximum
            active_only: Si True, seulement les produits actifs
            
        Returns:
            Liste de résultats filtrés
        """
        # Recherche initiale avec plus de résultats pour compenser le filtrage
        initial_k = min(k * 3, MAX_SEARCH_K)
        results = self.search(query, k=initial_k)
        
        if not results:
            return results
        
        # Importer ici pour éviter les imports circulaires
        from catalog.models import Product
        
        # Obtenir les IDs des produits
        product_ids = [result[0] for result in results]
        
        # Construire le queryset avec filtres
        queryset = Product.objects.filter(id__in=product_ids)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        if category_ids:
            queryset = queryset.filter(category_id__in=category_ids)
        
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        # Obtenir les IDs filtrés
        filtered_ids = set(queryset.values_list('id', flat=True))
        
        # Filtrer les résultats
        filtered_results = [
            result for result in results 
            if result[0] in filtered_ids
        ]
        
        return filtered_results[:k]
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur l'index.
        
        Returns:
            Dictionnaire avec les informations de l'index
        """
        if self.index is None:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "total_vectors": self.index.ntotal,
            "dimension": self.index.d,
            "product_count": len(self.product_ids),
            "index_type": "FAISS_IndexFlatIP",
        }

