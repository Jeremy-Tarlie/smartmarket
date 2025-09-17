#!/usr/bin/env python
"""
Script de démonstration des fonctionnalités ML de SmartMarket.
"""

import os
import sys
import django
import json
import time
from pathlib import Path

# Configuration Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartmarket.settings.dev')
django.setup()

from catalog.models import Product, Category
from catalog.ml_views import recommendation_engine, search_engine, rag_service
from ml.manifest import ml_manifest
from ml.cache import ml_cache


def print_header(title):
    """Affiche un en-tête formaté."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_section(title):
    """Affiche un titre de section."""
    print(f"\n--- {title} ---")


def demo_manifest():
    """Démonstration du manifest ML."""
    print_header("MANIFEST ML - ÉTAT DES ARTEFACTS")
    
    try:
        summary = ml_manifest.get_manifest_summary()
        print(f"Version du manifest : {summary['version']}")
        print(f"Créé le : {summary['created_at']}")
        print(f"Mis à jour le : {summary['updated_at']}")
        print(f"Total artefacts : {summary['total_artifacts']}")
        print(f"Total modèles : {summary['total_models']}")
        print(f"Total index : {summary['total_indexes']}")
        
        if summary['artifacts']:
            print_section("Artefacts")
            for artifact in summary['artifacts']:
                print(f"  - {artifact}")
        
        if summary['models']:
            print_section("Modèles")
            for model in summary['models']:
                print(f"  - {model}")
        
        if summary['indexes']:
            print_section("Index")
            for index in summary['indexes']:
                print(f"  - {index}")
        
        # Validation
        validation = ml_manifest.validate_artifacts()
        print_section("Validation")
        print(f"Artefacts valides : {'✅' if validation['valid'] else '❌'}")
        if validation['missing_files']:
            print("Fichiers manquants :")
            for file in validation['missing_files']:
                print(f"  - {file}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'accès au manifest : {e}")


def demo_cache():
    """Démonstration du cache Redis."""
    print_header("CACHE REDIS - STATISTIQUES")
    
    try:
        stats = ml_cache.get_cache_stats()
        print(f"Statut : {stats['status']}")
        
        if stats['status'] == 'connected':
            print(f"Total clés : {stats['total_keys']}")
            print(f"Clés ML : {stats['ml_keys']}")
            print(f"Utilisation mémoire : {stats['memory_usage']}")
            print(f"Uptime : {stats['uptime']} secondes")
        else:
            print("⚠️ Redis non disponible")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'accès au cache : {e}")


def demo_products():
    """Affiche les produits disponibles."""
    print_header("PRODUITS DISPONIBLES")
    
    try:
        products = Product.objects.filter(is_active=True)[:5]
        print(f"Total produits actifs : {Product.objects.filter(is_active=True).count()}")
        
        for product in products:
            print(f"  {product.id}: {product.name} - {product.category.name} - {product.price}€")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'accès aux produits : {e}")


def demo_recommendations():
    """Démonstration des recommandations."""
    print_header("RECOMMANDATIONS - DÉMONSTRATION")
    
    try:
        # Obtenir un produit de test
        product = Product.objects.filter(is_active=True).first()
        if not product:
            print("❌ Aucun produit disponible pour les tests")
            return
        
        print(f"Produit de test : {product.name} (ID: {product.id})")
        
        # Test des recommandations
        print_section("Recommandations standard")
        start_time = time.time()
        recommendations = recommendation_engine.get_recommendations(product.id, k=5)
        response_time = (time.time() - start_time) * 1000
        
        print(f"Temps de réponse : {response_time:.2f}ms")
        print(f"Nombre de recommandations : {len(recommendations)}")
        
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec['name']} - Score: {rec['similarity_score']} - {rec['reason']}")
        
        # Test avec diversité
        print_section("Recommandations avec diversité (MMR)")
        start_time = time.time()
        diverse_recs = recommendation_engine.get_recommendations(product.id, k=5, use_diversity=True)
        response_time = (time.time() - start_time) * 1000
        
        print(f"Temps de réponse : {response_time:.2f}ms")
        print(f"Nombre de recommandations : {len(diverse_recs)}")
        
        for i, rec in enumerate(diverse_recs[:3], 1):
            print(f"  {i}. {rec['name']} - Score: {rec['similarity_score']} - {rec['reason']}")
            
    except Exception as e:
        print(f"❌ Erreur lors des recommandations : {e}")


def demo_search():
    """Démonstration de la recherche sémantique."""
    print_header("RECHERCHE SÉMANTIQUE - DÉMONSTRATION")
    
    try:
        # Tests de recherche
        test_queries = [
            "smartphone",
            "vêtement",
            "électronique",
            "prix bas"
        ]
        
        for query in test_queries:
            print_section(f"Recherche : '{query}'")
            
            start_time = time.time()
            results = search_engine.search(query, k=5)
            response_time = (time.time() - start_time) * 1000
            
            print(f"Temps de réponse : {response_time:.2f}ms")
            print(f"Nombre de résultats : {len(results)}")
            
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result['name']} - Score: {result['search_score']} - {result['reason']}")
                
    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")


def demo_rag():
    """Démonstration de l'assistant RAG."""
    print_header("ASSISTANT RAG - DÉMONSTRATION")
    
    try:
        # Tests de questions
        test_questions = [
            "Quelle est votre politique de retour ?",
            "Comment fonctionne la livraison ?",
            "Quels sont les délais de livraison ?",
            "Comment choisir la bonne taille de vêtement ?",
            "Quelle est la garantie des produits électroniques ?"
        ]
        
        for question in test_questions:
            print_section(f"Question : '{question}'")
            
            start_time = time.time()
            response = rag_service.ask_question(question)
            response_time = (time.time() - start_time) * 1000
            
            print(f"Temps de réponse : {response_time:.2f}ms")
            print(f"Statut : {response['status']}")
            print(f"Confiance : {response['confidence']:.2f}")
            print(f"Trace ID : {response['trace_id']}")
            
            print("Réponse :")
            print(f"  {response['answer'][:200]}{'...' if len(response['answer']) > 200 else ''}")
            
            if response['sources']:
                print(f"Sources ({len(response['sources'])}):")
                for i, source in enumerate(response['sources'][:2], 1):
                    print(f"  {i}. Score: {source['score']:.2f} - {source['metadata'].get('title', 'Sans titre')}")
            
            print()  # Ligne vide entre les questions
            
    except Exception as e:
        print(f"❌ Erreur lors des tests RAG : {e}")


def demo_performance():
    """Démonstration des performances."""
    print_header("PERFORMANCES - MÉTRIQUES")
    
    try:
        # Test de charge simple
        product = Product.objects.filter(is_active=True).first()
        if not product:
            print("❌ Aucun produit disponible pour les tests")
            return
        
        print_section("Test de charge - Recommandations")
        times = []
        for i in range(10):
            start_time = time.time()
            recommendations = recommendation_engine.get_recommendations(product.id, k=5)
            response_time = (time.time() - start_time) * 1000
            times.append(response_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"Temps moyen : {avg_time:.2f}ms")
        print(f"Temps max : {max_time:.2f}ms")
        print(f"Temps min : {min_time:.2f}ms")
        print(f"Objectif P95 ≤ 150ms : {'✅' if max_time <= 150 else '❌'}")
        
        print_section("Test de charge - Recherche")
        times = []
        for i in range(10):
            start_time = time.time()
            results = search_engine.search("test", k=5)
            response_time = (time.time() - start_time) * 1000
            times.append(response_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"Temps moyen : {avg_time:.2f}ms")
        print(f"Temps max : {max_time:.2f}ms")
        print(f"Objectif P95 ≤ 300ms : {'✅' if max_time <= 300 else '❌'}")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests de performance : {e}")


def main():
    """Fonction principale de démonstration."""
    print("🚀 DÉMONSTRATION DES FONCTIONNALITÉS ML - SMARTMARKET")
    print("=" * 60)
    
    # Vérifications préliminaires
    print("Vérification des prérequis...")
    
    # Manifest
    demo_manifest()
    
    # Cache
    demo_cache()
    
    # Produits
    demo_products()
    
    # Recommandations
    demo_recommendations()
    
    # Recherche
    demo_search()
    
    # RAG
    demo_rag()
    
    # Performances
    demo_performance()
    
    print_header("DÉMONSTRATION TERMINÉE")
    print("✅ Toutes les fonctionnalités ML ont été testées")
    print("\nPour plus d'informations, consultez README_ML.md")


if __name__ == "__main__":
    main()

