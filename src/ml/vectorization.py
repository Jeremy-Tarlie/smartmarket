"""
Vectorisation des produits pour les recommandations et la recherche.
"""

import pickle
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

from .config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    TFIDF_MODEL_PATH,
    PRODUCT_EMBEDDINGS_PATH,
)
from .preprocessing import create_product_text


class ProductVectorizer:
    """Classe pour vectoriser les produits."""
    
    def __init__(self):
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self.product_ids: List[int] = []
        self.product_texts: List[str] = []
        
    def load_models(self):
        """Charge les modèles pré-entraînés."""
        # Charger le modèle TF-IDF
        if TFIDF_MODEL_PATH.exists():
            with open(TFIDF_MODEL_PATH, 'rb') as f:
                self.tfidf_vectorizer = pickle.load(f)
        
        # Charger le modèle d'embeddings
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            print(f"Erreur lors du chargement du modèle d'embeddings: {e}")
            self.embedding_model = None
    
    def prepare_data(self, products):
        """
        Prépare les données des produits pour la vectorisation.
        
        Args:
            products: QuerySet des produits
        """
        self.product_ids = []
        self.product_texts = []
        
        for product in products:
            if product.is_active:  # Seulement les produits actifs
                self.product_ids.append(product.id)
                text = create_product_text(product)
                self.product_texts.append(text)
    
    def fit_tfidf(self, products):
        """
        Entraîne le modèle TF-IDF sur les produits.
        
        Args:
            products: QuerySet des produits
        """
        self.prepare_data(products)
        
        if not self.product_texts:
            raise ValueError("Aucun texte de produit disponible")
        
        # Configuration TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2),
            stop_words=None,  # Déjà géré dans preprocessing
        )
        
        # Entraîner le modèle
        self.tfidf_vectorizer.fit(self.product_texts)
        
        # Sauvegarder le modèle
        with open(TFIDF_MODEL_PATH, 'wb') as f:
            pickle.dump(self.tfidf_vectorizer, f)
    
    def get_tfidf_vectors(self, products=None) -> np.ndarray:
        """
        Obtient les vecteurs TF-IDF pour les produits.
        
        Args:
            products: QuerySet des produits (optionnel, utilise les données préparées si None)
            
        Returns:
            Matrice des vecteurs TF-IDF
        """
        if products is not None:
            self.prepare_data(products)
        
        if not self.tfidf_vectorizer:
            raise ValueError("Modèle TF-IDF non entraîné")
        
        if not self.product_texts:
            raise ValueError("Aucun texte de produit disponible")
        
        return self.tfidf_vectorizer.transform(self.product_texts).toarray()
    
    def get_embeddings(self, products=None) -> np.ndarray:
        """
        Obtient les embeddings sémantiques pour les produits.
        
        Args:
            products: QuerySet des produits (optionnel, utilise les données préparées si None)
            
        Returns:
            Matrice des embeddings
        """
        if products is not None:
            self.prepare_data(products)
        
        if not self.embedding_model:
            raise ValueError("Modèle d'embeddings non chargé")
        
        if not self.product_texts:
            raise ValueError("Aucun texte de produit disponible")
        
        # Générer les embeddings
        embeddings = self.embedding_model.encode(
            self.product_texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def save_embeddings(self, embeddings: np.ndarray):
        """
        Sauvegarde les embeddings des produits.
        
        Args:
            embeddings: Matrice des embeddings
        """
        np.save(PRODUCT_EMBEDDINGS_PATH, embeddings)
        
        # Sauvegarder aussi les IDs des produits
        ids_path = PRODUCT_EMBEDDINGS_PATH.with_suffix('.ids.pkl')
        with open(ids_path, 'wb') as f:
            pickle.dump(self.product_ids, f)
    
    def load_embeddings(self) -> Tuple[np.ndarray, List[int]]:
        """
        Charge les embeddings sauvegardés.
        
        Returns:
            Tuple (embeddings, product_ids)
        """
        if not PRODUCT_EMBEDDINGS_PATH.exists():
            raise FileNotFoundError("Embeddings non trouvés")
        
        embeddings = np.load(PRODUCT_EMBEDDINGS_PATH)
        
        # Charger les IDs des produits
        ids_path = PRODUCT_EMBEDDINGS_PATH.with_suffix('.ids.pkl')
        if ids_path.exists():
            with open(ids_path, 'rb') as f:
                product_ids = pickle.load(f)
        else:
            product_ids = []
        
        return embeddings, product_ids
    
    def get_product_embedding(self, product) -> np.ndarray:
        """
        Obtient l'embedding pour un produit spécifique.
        
        Args:
            product: Instance du modèle Product
            
        Returns:
            Embedding du produit
        """
        if not self.embedding_model:
            raise ValueError("Modèle d'embeddings non chargé")
        
        text = create_product_text(product)
        return self.embedding_model.encode([text])[0]
    
    def get_product_tfidf_vector(self, product) -> np.ndarray:
        """
        Obtient le vecteur TF-IDF pour un produit spécifique.
        
        Args:
            product: Instance du modèle Product
            
        Returns:
            Vecteur TF-IDF du produit
        """
        if not self.tfidf_vectorizer:
            raise ValueError("Modèle TF-IDF non entraîné")
        
        text = create_product_text(product)
        return self.tfidf_vectorizer.transform([text]).toarray()[0]

