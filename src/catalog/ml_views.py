"""
Vues API pour les fonctionnalités ML (recommandations, recherche, RAG).
"""

import time
from typing import Dict, Any, List
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Category
from .serializers import ProductSerializer

# Import des modules ML
from ml.vectorization import ProductVectorizer
from ml.similarity import SimilarityEngine
from ml.search import SemanticSearchEngine
from ml.rag import RAGAssistant
from ml.cache import ml_cache
from ml.manifest import ml_manifest


class MLThrottle(UserRateThrottle):
    """Throttling pour les endpoints ML."""
    scope = 'ml_requests'


class RecommendationEngine:
    """Moteur de recommandations."""
    
    def __init__(self):
        self.vectorizer = ProductVectorizer()
        self.similarity_engine = SimilarityEngine()
        self._initialized = False
    
    def _initialize(self):
        """Initialise le moteur de recommandations."""
        if self._initialized:
            return
        
        try:
            # Charger les modèles
            self.vectorizer.load_models()
            
            # Charger les embeddings
            embeddings, product_ids = self.vectorizer.load_embeddings()
            
            # Initialiser le moteur de similarité
            self.similarity_engine.load_embeddings(embeddings, product_ids)
            
            self._initialized = True
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation du moteur de recommandations: {e}")
            self._initialized = False
    
    def get_recommendations(
        self,
        product_id: int,
        k: int = 10,
        use_diversity: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Obtient les recommandations pour un produit.
        
        Args:
            product_id: ID du produit
            k: Nombre de recommandations
            use_diversity: Si True, utilise MMR pour la diversité
            
        Returns:
            Liste des recommandations
        """
        if not self._initialized:
            self._initialize()
        
        if not self._initialized:
            return []
        
        # Vérifier le cache
        cache_key = {
            'product_id': product_id,
            'k': k,
            'use_diversity': use_diversity
        }
        
        cached_result = ml_cache.get('recommendations', **cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Obtenir les recommandations
            if use_diversity:
                recommendations = self.similarity_engine.get_diverse_recommendations(
                    product_id, k=k
                )
            else:
                recommendations = self.similarity_engine.get_similar_products(
                    product_id, k=k
                )
            
            # Formater les résultats
            result = []
            for rec_id, score, reason in recommendations:
                try:
                    product = Product.objects.get(id=rec_id, is_active=True)
                    product_data = ProductSerializer(product).data
                    product_data['similarity_score'] = round(score, 3)
                    product_data['reason'] = reason
                    result.append(product_data)
                except Product.DoesNotExist:
                    continue
            
            # Mettre en cache
            ml_cache.set('recommendations', result, **cache_key)
            
            return result
            
        except Exception as e:
            print(f"Erreur lors de l'obtention des recommandations: {e}")
            return []


class SearchEngine:
    """Moteur de recherche sémantique."""
    
    def __init__(self):
        self.search_engine = SemanticSearchEngine()
        self.vectorizer = ProductVectorizer()
        self._initialized = False
    
    def _initialize(self):
        """Initialise le moteur de recherche."""
        if self._initialized:
            return
        
        try:
            # Charger les modèles
            self.vectorizer.load_models()
            self.search_engine.load_embedding_model(self.vectorizer.embedding_model)
            
            # Charger l'index
            self.search_engine.load_index()
            
            self._initialized = True
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation du moteur de recherche: {e}")
            self._initialized = False
    
    def search(
        self,
        query: str,
        k: int = 20,
        category_ids: List[int] = None,
        min_price: float = None,
        max_price: float = None
    ) -> List[Dict[str, Any]]:
        """
        Effectue une recherche sémantique.
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats
            category_ids: IDs des catégories à filtrer
            min_price: Prix minimum
            max_price: Prix maximum
            
        Returns:
            Liste des résultats
        """
        if not self._initialized:
            self._initialize()
        
        if not self._initialized:
            return []
        
        # Vérifier le cache
        cache_key = {
            'query': query,
            'k': k,
            'category_ids': category_ids,
            'min_price': min_price,
            'max_price': max_price
        }
        
        cached_result = ml_cache.get('search', **cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Effectuer la recherche
            search_results = self.search_engine.search_with_filters(
                query=query,
                k=k,
                category_ids=category_ids,
                min_price=min_price,
                max_price=max_price
            )
            
            # Formater les résultats
            result = []
            for product_id, score, reason in search_results:
                try:
                    product = Product.objects.get(id=product_id, is_active=True)
                    product_data = ProductSerializer(product).data
                    product_data['search_score'] = round(score, 3)
                    product_data['reason'] = reason
                    result.append(product_data)
                except Product.DoesNotExist:
                    continue
            
            # Mettre en cache
            ml_cache.set('search', result, **cache_key)
            
            return result
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []


class RAGService:
    """Service RAG pour l'assistant."""
    
    def __init__(self):
        self.rag_assistant = RAGAssistant()
        self._initialized = False
    
    def _initialize(self):
        """Initialise le service RAG."""
        if self._initialized:
            return
        
        try:
            # Charger l'index RAG
            self.rag_assistant.load_index()
            self._initialized = True
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation du service RAG: {e}")
            self._initialized = False
    
    def ask_question(
        self,
        question: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Pose une question à l'assistant RAG.
        
        Args:
            question: Question de l'utilisateur
            user_context: Contexte utilisateur
            
        Returns:
            Réponse de l'assistant
        """
        if not self._initialized:
            self._initialize()
        
        if not self._initialized:
            return {
                'answer': "L'assistant n'est pas disponible pour le moment.",
                'sources': [],
                'trace_id': None,
                'confidence': 0.0,
                'status': 'error'
            }
        
        try:
            # Poser la question
            response = self.rag_assistant.ask(question, user_context)
            
            return response
            
        except Exception as e:
            print(f"Erreur lors de la question RAG: {e}")
            return {
                'answer': "Une erreur s'est produite lors du traitement de votre question.",
                'sources': [],
                'trace_id': None,
                'confidence': 0.0,
                'status': 'error',
                'error': str(e)
            }


# Instances globales
recommendation_engine = RecommendationEngine()
search_engine = SearchEngine()
rag_service = RAGService()


@api_view(['GET'])
@throttle_classes([MLThrottle])
def product_recommendations(request, product_id):
    """
    Endpoint pour obtenir les recommandations d'un produit.
    
    GET /api/v1/products/{id}/recommendations/
    """
    start_time = time.time()
    
    try:
        # Vérifier que le produit existe
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Produit non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Paramètres de la requête
    k = min(int(request.GET.get('k', 10)), 50)  # Limiter à 50
    use_diversity = request.GET.get('diversity', 'false').lower() == 'true'
    
    # Obtenir les recommandations
    recommendations = recommendation_engine.get_recommendations(
        product_id=product_id,
        k=k,
        use_diversity=use_diversity
    )
    
    # Calculer le temps de réponse
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return Response({
        'product_id': product_id,
        'product_name': product.name,
        'recommendations': recommendations,
        'count': len(recommendations),
        'parameters': {
            'k': k,
            'use_diversity': use_diversity
        },
        'response_time_ms': response_time,
        'status': 'success'
    })


@api_view(['GET'])
@throttle_classes([MLThrottle])
def semantic_search(request):
    """
    Endpoint pour la recherche sémantique.
    
    GET /api/v1/search?q=...
    """
    start_time = time.time()
    
    # Paramètres de la requête
    query = request.GET.get('q', '').strip()
    if not query:
        return Response(
            {'error': 'Paramètre q (query) requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    k = min(int(request.GET.get('k', 20)), 100)  # Limiter à 100
    
    # Filtres optionnels
    category_ids = None
    if request.GET.get('category'):
        try:
            category_ids = [int(cat_id) for cat_id in request.GET.get('category').split(',')]
        except ValueError:
            return Response(
                {'error': 'IDs de catégorie invalides'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            min_price = float(min_price)
        except ValueError:
            return Response(
                {'error': 'Prix minimum invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            max_price = float(max_price)
        except ValueError:
            return Response(
                {'error': 'Prix maximum invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Effectuer la recherche
    results = search_engine.search(
        query=query,
        k=k,
        category_ids=category_ids,
        min_price=min_price,
        max_price=max_price
    )
    
    # Calculer le temps de réponse
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return Response({
        'query': query,
        'results': results,
        'count': len(results),
        'parameters': {
            'k': k,
            'category_ids': category_ids,
            'min_price': min_price,
            'max_price': max_price
        },
        'response_time_ms': response_time,
        'status': 'success'
    })


@api_view(['POST'])
@throttle_classes([MLThrottle])
def rag_assistant(request):
    """
    Endpoint pour l'assistant RAG.
    
    POST /api/v1/assistant/ask
    """
    start_time = time.time()
    
    # Vérifier les données de la requête
    question = request.data.get('question', '').strip()
    if not question:
        return Response(
            {'error': 'Paramètre question requis'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Contexte utilisateur optionnel
    user_context = request.data.get('user_context', {})
    
    # Poser la question à l'assistant
    response = rag_service.ask_question(
        question=question,
        user_context=user_context
    )
    
    # Calculer le temps de réponse
    response_time = round((time.time() - start_time) * 1000, 2)
    response['response_time_ms'] = response_time
    
    return Response(response)


@api_view(['GET'])
def ml_status(request):
    """
    Endpoint pour vérifier le statut des services ML.
    
    GET /api/v1/ml/status/
    """
    try:
        # Statut du cache
        cache_stats = ml_cache.get_cache_stats()
        
        # Statut du manifest
        manifest_summary = ml_manifest.get_manifest_summary()
        
        # Validation des artefacts
        validation_report = ml_manifest.validate_artifacts()
        
        return Response({
            'cache': cache_stats,
            'manifest': manifest_summary,
            'validation': validation_report,
            'services': {
                'recommendations': recommendation_engine._initialized,
                'search': search_engine._initialized,
                'rag': rag_service._initialized,
            }
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

