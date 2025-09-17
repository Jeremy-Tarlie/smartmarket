"""
Calcul de similarité et recommandations basées contenu.
"""

from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .config import DEFAULT_RECOMMENDATIONS_K, MAX_RECOMMENDATIONS_K


class SimilarityEngine:
    """Moteur de calcul de similarité pour les recommandations."""
    
    def __init__(self):
        self.product_embeddings: np.ndarray = None
        self.product_ids: List[int] = None
        self.id_to_index: Dict[int, int] = {}
    
    def load_embeddings(self, embeddings: np.ndarray, product_ids: List[int]):
        """
        Charge les embeddings et IDs des produits.
        
        Args:
            embeddings: Matrice des embeddings
            product_ids: Liste des IDs des produits
        """
        self.product_embeddings = embeddings
        self.product_ids = product_ids
        
        # Créer le mapping ID -> index
        self.id_to_index = {pid: idx for idx, pid in enumerate(product_ids)}
    
    def cosine_similarity_matrix(self) -> np.ndarray:
        """
        Calcule la matrice de similarité cosinus.
        
        Returns:
            Matrice de similarité
        """
        if self.product_embeddings is None:
            raise ValueError("Embeddings non chargés")
        
        return cosine_similarity(self.product_embeddings)
    
    def get_similar_products(
        self,
        product_id: int,
        k: int = DEFAULT_RECOMMENDATIONS_K,
        exclude_self: bool = True,
        min_similarity: float = 0.1
    ) -> List[Tuple[int, float, str]]:
        """
        Trouve les produits similaires à un produit donné.
        
        Args:
            product_id: ID du produit de référence
            k: Nombre de recommandations à retourner
            exclude_self: Si True, exclut le produit lui-même
            min_similarity: Similarité minimale requise
            
        Returns:
            Liste de tuples (product_id, similarity_score, reason)
        """
        if product_id not in self.id_to_index:
            return []
        
        # Limiter k
        k = min(k, MAX_RECOMMENDATIONS_K)
        
        # Calculer la matrice de similarité
        similarity_matrix = self.cosine_similarity_matrix()
        
        # Obtenir l'index du produit
        product_index = self.id_to_index[product_id]
        
        # Obtenir les similarités pour ce produit
        similarities = similarity_matrix[product_index]
        
        # Créer la liste des résultats avec indices
        results = []
        for idx, similarity in enumerate(similarities):
            if similarity >= min_similarity:
                if exclude_self and idx == product_index:
                    continue
                results.append((idx, similarity))
        
        # Trier par similarité décroissante
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Prendre les k premiers et formater
        recommendations = []
        for idx, similarity in results[:k]:
            pid = self.product_ids[idx]
            reason = self._generate_reason(product_id, pid, similarity)
            recommendations.append((pid, similarity, reason))
        
        return recommendations
    
    def _generate_reason(self, source_id: int, target_id: int, similarity: float) -> str:
        """
        Génère une raison pour la recommandation.
        
        Args:
            source_id: ID du produit source
            target_id: ID du produit cible
            similarity: Score de similarité
            
        Returns:
            Raison de la recommandation
        """
        if similarity > 0.8:
            return "Très similaire par caractéristiques"
        elif similarity > 0.6:
            return "Similaire par catégorie et caractéristiques"
        elif similarity > 0.4:
            return "Similaire par catégorie"
        else:
            return "Produit complémentaire"
    
    def get_diverse_recommendations(
        self,
        product_id: int,
        k: int = DEFAULT_RECOMMENDATIONS_K,
        diversity_weight: float = 0.3
    ) -> List[Tuple[int, float, str]]:
        """
        Trouve des recommandations diversifiées en utilisant MMR (Maximal Marginal Relevance).
        
        Args:
            product_id: ID du produit de référence
            k: Nombre de recommandations à retourner
            diversity_weight: Poids de la diversité (0 = pas de diversité, 1 = diversité maximale)
            
        Returns:
            Liste de recommandations diversifiées
        """
        if product_id not in self.id_to_index:
            return []
        
        # Obtenir plus de candidats que nécessaire
        candidates = self.get_similar_products(
            product_id, 
            k=k*3,  # 3x plus de candidats
            exclude_self=True
        )
        
        if not candidates:
            return []
        
        # MMR simple
        selected = []
        remaining = candidates.copy()
        
        # Prendre le premier (le plus similaire)
        if remaining:
            selected.append(remaining.pop(0))
        
        # Sélectionner les suivants avec diversité
        while len(selected) < k and remaining:
            best_candidate = None
            best_score = -1
            
            for candidate in remaining:
                # Score de similarité
                similarity_score = candidate[1]
                
                # Score de diversité (distance minimale aux sélectionnés)
                diversity_score = 0
                if selected:
                    min_distance = min(
                        1 - self._get_similarity_between_products(
                            candidate[0], sel[0]
                        )
                        for sel in selected
                    )
                    diversity_score = min_distance
                
                # Score combiné
                combined_score = (
                    (1 - diversity_weight) * similarity_score + 
                    diversity_weight * diversity_score
                )
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
            else:
                break
        
        return selected
    
    def _get_similarity_between_products(self, product_id1: int, product_id2: int) -> float:
        """
        Calcule la similarité entre deux produits.
        
        Args:
            product_id1: ID du premier produit
            product_id2: ID du deuxième produit
            
        Returns:
            Score de similarité
        """
        if (product_id1 not in self.id_to_index or 
            product_id2 not in self.id_to_index):
            return 0.0
        
        idx1 = self.id_to_index[product_id1]
        idx2 = self.id_to_index[product_id2]
        
        similarity_matrix = self.cosine_similarity_matrix()
        return similarity_matrix[idx1, idx2]
    
    def batch_similarity(self, product_ids: List[int]) -> Dict[int, List[Tuple[int, float, str]]]:
        """
        Calcule les similarités pour plusieurs produits en lot.
        
        Args:
            product_ids: Liste des IDs des produits
            
        Returns:
            Dictionnaire {product_id: [(similar_id, score, reason), ...]}
        """
        results = {}
        
        for product_id in product_ids:
            results[product_id] = self.get_similar_products(product_id)
        
        return results

