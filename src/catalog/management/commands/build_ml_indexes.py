"""
Commande Django pour construire les index ML.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import Product
from ml.vectorization import ProductVectorizer
from ml.similarity import SimilarityEngine
from ml.search import SemanticSearchEngine
from ml.manifest import ml_manifest
from ml.cache import ml_cache
import time


class Command(BaseCommand):
    help = 'Construit les index ML pour les recommandations et la recherche sémantique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la reconstruction même si les index existent',
        )
        parser.add_argument(
            '--skip-cache-clear',
            action='store_true',
            help='Ne vide pas le cache après construction',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Début de la construction des index ML...')
        )
        
        try:
            # Vérifier les produits
            products = Product.objects.filter(is_active=True)
            product_count = products.count()
            
            if product_count == 0:
                raise CommandError('Aucun produit actif trouvé dans la base de données')
            
            self.stdout.write(f'📦 {product_count} produits actifs trouvés')
            
            # Initialiser le vectorizer
            self.stdout.write('🔧 Initialisation du vectorizer...')
            vectorizer = ProductVectorizer()
            
            # Entraîner le modèle TF-IDF
            self.stdout.write('📊 Entraînement du modèle TF-IDF...')
            vectorizer.fit_tfidf(products)
            
            # Générer les embeddings
            self.stdout.write('🧠 Génération des embeddings sémantiques...')
            embeddings = vectorizer.get_embeddings(products)
            
            # Sauvegarder les embeddings
            self.stdout.write('💾 Sauvegarde des embeddings...')
            vectorizer.save_embeddings(embeddings)
            
            # Construire l'index de recherche sémantique
            self.stdout.write('🔍 Construction de l\'index de recherche...')
            search_engine = SemanticSearchEngine()
            search_engine.load_embedding_model(vectorizer.embedding_model)
            search_engine.build_index(embeddings, vectorizer.product_ids)
            
            # Enregistrer dans le manifest
            self.stdout.write('📋 Mise à jour du manifest...')
            ml_manifest.register_model(
                name='tfidf_vectorizer',
                model_type='tfidf',
                version='1.0.0',
                file_path=str(vectorizer.tfidf_vectorizer.__class__.__module__),
                parameters={
                    'max_features': 5000,
                    'min_df': 2,
                    'max_df': 0.8,
                    'ngram_range': (1, 2),
                }
            )
            
            ml_manifest.register_model(
                name='embedding_model',
                model_type='sentence_transformer',
                version='1.0.0',
                file_path='sentence-transformers/all-MiniLM-L6-v2',
                parameters={
                    'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                    'dimension': embeddings.shape[1],
                }
            )
            
            ml_manifest.register_index(
                name='product_embeddings',
                index_type='numpy_array',
                file_path=str(vectorizer.product_embeddings_path),
                document_count=len(vectorizer.product_ids),
                metadata={
                    'product_ids': vectorizer.product_ids,
                    'embedding_dimension': embeddings.shape[1],
                }
            )
            
            ml_manifest.register_index(
                name='search_index',
                index_type='faiss',
                file_path=str(search_engine.faiss_index_path),
                document_count=len(vectorizer.product_ids),
                metadata={
                    'index_type': 'IndexFlatIP',
                    'dimension': embeddings.shape[1],
                }
            )
            
            # Vider le cache si demandé
            if not options['skip_cache_clear']:
                self.stdout.write('🗑️ Vidage du cache...')
                ml_cache.invalidate_all_cache()
            
            # Calculer le temps d'exécution
            execution_time = time.time() - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Construction terminée avec succès en {execution_time:.2f}s'
                )
            )
            
            # Afficher le résumé
            manifest_summary = ml_manifest.get_manifest_summary()
            self.stdout.write(f'📊 Résumé:')
            self.stdout.write(f'   - Modèles: {manifest_summary["total_models"]}')
            self.stdout.write(f'   - Index: {manifest_summary["total_indexes"]}')
            self.stdout.write(f'   - Artefacts: {manifest_summary["total_artifacts"]}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la construction: {e}')
            )
            raise CommandError(f'Échec de la construction des index: {e}')



