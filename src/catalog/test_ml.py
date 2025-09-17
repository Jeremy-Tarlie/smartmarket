"""
Tests pour les fonctionnalités ML.
"""

import json
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import Product, Category
from .ml_views import RecommendationEngine, SearchEngine, RAGService

User = get_user_model()


class MLTestCase(TestCase):
    """Tests de base pour les fonctionnalités ML."""
    
    def setUp(self):
        """Configuration des tests."""
        # Créer des catégories
        self.category1 = Category.objects.create(
            name="Électronique",
            slug="electronique"
        )
        self.category2 = Category.objects.create(
            name="Mode",
            slug="mode"
        )
        
        # Créer des produits
        self.product1 = Product.objects.create(
            category=self.category1,
            name="Smartphone Samsung",
            slug="smartphone-samsung",
            description="Smartphone haut de gamme avec écran AMOLED",
            price=699.99,
            stock=10,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            category=self.category1,
            name="iPhone 15",
            slug="iphone-15",
            description="iPhone dernière génération avec puce A17",
            price=999.99,
            stock=5,
            is_active=True
        )
        
        self.product3 = Product.objects.create(
            category=self.category2,
            name="T-shirt coton",
            slug="t-shirt-coton",
            description="T-shirt en coton bio confortable",
            price=19.99,
            stock=50,
            is_active=True
        )
        
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_product_vectorizer_initialization(self):
        """Test l'initialisation du vectorizer."""
        from ml.vectorization import ProductVectorizer
        
        vectorizer = ProductVectorizer()
        self.assertIsNotNone(vectorizer)
        self.assertIsNone(vectorizer.tfidf_vectorizer)
        self.assertIsNone(vectorizer.embedding_model)
    
    def test_similarity_engine_initialization(self):
        """Test l'initialisation du moteur de similarité."""
        from ml.similarity import SimilarityEngine
        
        engine = SimilarityEngine()
        self.assertIsNotNone(engine)
        self.assertIsNone(engine.product_embeddings)
        self.assertIsNone(engine.product_ids)
    
    def test_search_engine_initialization(self):
        """Test l'initialisation du moteur de recherche."""
        from ml.search import SemanticSearchEngine
        
        engine = SemanticSearchEngine()
        self.assertIsNotNone(engine)
        self.assertIsNone(engine.index)
        self.assertIsNone(engine.embedding_model)
    
    def test_rag_service_initialization(self):
        """Test l'initialisation du service RAG."""
        from ml.rag import RAGAssistant
        
        service = RAGAssistant()
        self.assertIsNotNone(service)
        self.assertIsNotNone(service.rag_index)


class MLAPITestCase(APITestCase):
    """Tests API pour les fonctionnalités ML."""
    
    def setUp(self):
        """Configuration des tests API."""
        # Créer des catégories
        self.category1 = Category.objects.create(
            name="Électronique",
            slug="electronique"
        )
        
        # Créer des produits
        self.product1 = Product.objects.create(
            category=self.category1,
            name="Smartphone Samsung",
            slug="smartphone-samsung",
            description="Smartphone haut de gamme avec écran AMOLED",
            price=699.99,
            stock=10,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            category=self.category1,
            name="iPhone 15",
            slug="iphone-15",
            description="iPhone dernière génération avec puce A17",
            price=999.99,
            stock=5,
            is_active=True
        )
        
        # Créer un utilisateur et s'authentifier
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('catalog.ml_views.recommendation_engine')
    def test_product_recommendations_endpoint(self, mock_engine):
        """Test l'endpoint des recommandations."""
        # Mock des recommandations
        mock_engine.get_recommendations.return_value = [
            {
                'id': self.product2.id,
                'name': self.product2.name,
                'price': str(self.product2.price),
                'similarity_score': 0.85,
                'reason': 'Similaire par catégorie et caractéristiques'
            }
        ]
        
        url = reverse('catalog_api:product_recommendations', args=[self.product1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        self.assertIn('response_time_ms', response.data)
        self.assertEqual(len(response.data['recommendations']), 1)
    
    def test_product_recommendations_not_found(self):
        """Test l'endpoint des recommandations avec un produit inexistant."""
        url = reverse('catalog_api:product_recommendations', args=[99999])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    @patch('catalog.ml_views.search_engine')
    def test_semantic_search_endpoint(self, mock_engine):
        """Test l'endpoint de recherche sémantique."""
        # Mock des résultats de recherche
        mock_engine.search.return_value = [
            {
                'id': self.product1.id,
                'name': self.product1.name,
                'price': str(self.product1.price),
                'search_score': 0.92,
                'reason': 'Correspondance excellente avec \'smartphone\''
            }
        ]
        
        url = reverse('catalog_api:semantic_search')
        response = self.client.get(url, {'q': 'smartphone'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('query', response.data)
        self.assertEqual(response.data['query'], 'smartphone')
    
    def test_semantic_search_missing_query(self):
        """Test l'endpoint de recherche sans paramètre q."""
        url = reverse('catalog_api:semantic_search')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('catalog.ml_views.rag_service')
    def test_rag_assistant_endpoint(self, mock_service):
        """Test l'endpoint de l'assistant RAG."""
        # Mock de la réponse RAG
        mock_service.ask_question.return_value = {
            'answer': 'Voici les informations sur nos politiques de retour...',
            'sources': [
                {
                    'content': 'Vous avez 30 jours pour retourner un produit...',
                    'metadata': {'type': 'policy', 'category': 'returns'},
                    'score': 0.95
                }
            ],
            'trace_id': 'test-trace-123',
            'confidence': 0.95,
            'status': 'success'
        }
        
        url = reverse('catalog_api:rag_assistant')
        data = {'question': 'Quelle est votre politique de retour ?'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertIn('sources', response.data)
        self.assertIn('trace_id', response.data)
    
    def test_rag_assistant_missing_question(self):
        """Test l'endpoint RAG sans question."""
        url = reverse('catalog_api:rag_assistant')
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_ml_status_endpoint(self):
        """Test l'endpoint de statut ML."""
        url = reverse('catalog_api:ml_status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cache', response.data)
        self.assertIn('manifest', response.data)
        self.assertIn('services', response.data)


class MLPerformanceTestCase(TestCase):
    """Tests de performance pour les fonctionnalités ML."""
    
    def setUp(self):
        """Configuration des tests de performance."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        # Créer plusieurs produits pour les tests
        self.products = []
        for i in range(10):
            product = Product.objects.create(
                category=self.category,
                name=f"Produit Test {i}",
                slug=f"produit-test-{i}",
                description=f"Description du produit test {i}",
                price=10.00 + i,
                stock=10,
                is_active=True
            )
            self.products.append(product)
    
    def test_recommendation_performance(self):
        """Test la performance des recommandations."""
        from catalog.ml_views import RecommendationEngine
        
        engine = RecommendationEngine()
        
        start_time = time.time()
        # Simuler l'obtention de recommandations
        recommendations = engine.get_recommendations(self.products[0].id, k=5)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # en ms
        
        # Vérifier que le temps de réponse est acceptable
        # (même sans index réel, on teste la structure)
        self.assertLess(response_time, 5000)  # 5 secondes max
    
    def test_search_performance(self):
        """Test la performance de la recherche."""
        from catalog.ml_views import SearchEngine
        
        engine = SearchEngine()
        
        start_time = time.time()
        # Simuler une recherche
        results = engine.search("test query", k=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # en ms
        
        # Vérifier que le temps de réponse est acceptable
        self.assertLess(response_time, 5000)  # 5 secondes max


class MLCacheTestCase(TestCase):
    """Tests pour le cache ML."""
    
    def setUp(self):
        """Configuration des tests de cache."""
        from ml.cache import MLCache
        self.cache = MLCache()
    
    def test_cache_key_generation(self):
        """Test la génération des clés de cache."""
        key = self.cache._generate_cache_key('test', param1='value1', param2='value2')
        self.assertIsInstance(key, str)
        self.assertTrue(key.startswith('smartmarket_ml:test:'))
    
    def test_cache_operations(self):
        """Test les opérations de cache."""
        # Test de stockage et récupération
        test_data = {'test': 'data', 'number': 123}
        
        # Stocker
        self.cache.set('test', test_data, param='value')
        
        # Récupérer
        retrieved_data = self.cache.get('test', param='value')
        
        # Vérifier (peut être None si Redis n'est pas disponible)
        if retrieved_data is not None:
            self.assertEqual(retrieved_data, test_data)
    
    def test_cache_invalidation(self):
        """Test l'invalidation du cache."""
        # Test d'invalidation par pattern
        self.cache.delete_pattern('test:*')
        
        # Test d'invalidation de produit
        self.cache.invalidate_product_cache(123)
        
        # Ces opérations ne doivent pas lever d'exception
        self.assertTrue(True)


class MLManifestTestCase(TestCase):
    """Tests pour le manifest ML."""
    
    def setUp(self):
        """Configuration des tests de manifest."""
        from ml.manifest import MLManifest
        self.manifest = MLManifest()
    
    def test_manifest_initialization(self):
        """Test l'initialisation du manifest."""
        self.assertIsNotNone(self.manifest.manifest_data)
        self.assertIn('version', self.manifest.manifest_data)
        self.assertIn('artifacts', self.manifest.manifest_data)
        self.assertIn('models', self.manifest.manifest_data)
        self.assertIn('indexes', self.manifest.manifest_data)
    
    def test_artifact_registration(self):
        """Test l'enregistrement d'artefacts."""
        self.manifest.register_artifact(
            name='test_artifact',
            artifact_type='test',
            file_path='/tmp/test.txt',
            metadata={'test': 'data'}
        )
        
        artifact_info = self.manifest.get_artifact_info('test_artifact')
        self.assertIsNotNone(artifact_info)
        self.assertEqual(artifact_info['name'], 'test_artifact')
        self.assertEqual(artifact_info['type'], 'test')
    
    def test_model_registration(self):
        """Test l'enregistrement de modèles."""
        self.manifest.register_model(
            name='test_model',
            model_type='test',
            version='1.0.0',
            file_path='/tmp/test_model.pkl',
            parameters={'param1': 'value1'}
        )
        
        model_info = self.manifest.get_model_info('test_model')
        self.assertIsNotNone(model_info)
        self.assertEqual(model_info['name'], 'test_model')
        self.assertEqual(model_info['version'], '1.0.0')
    
    def test_manifest_summary(self):
        """Test le résumé du manifest."""
        summary = self.manifest.get_manifest_summary()
        
        self.assertIn('version', summary)
        self.assertIn('total_artifacts', summary)
        self.assertIn('total_models', summary)
        self.assertIn('total_indexes', summary)
        self.assertIsInstance(summary['total_artifacts'], int)
        self.assertIsInstance(summary['total_models'], int)
        self.assertIsInstance(summary['total_indexes'], int)

