#!/usr/bin/env python
"""
Script de test de pertinence pour évaluer les fonctionnalités ML.
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


def load_test_cases():
    """Charge les cas de test depuis le fichier JSON."""
    test_file = Path(__file__).parent / "test_data" / "relevance_test_cases.json"
    
    if not test_file.exists():
        print(f"❌ Fichier de test non trouvé : {test_file}")
        return None
    
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_recommendations(test_cases):
    """Test la pertinence des recommandations."""
    print("\n🔍 TEST DES RECOMMANDATIONS")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in test_cases.get('recommendations', []):
        product_id = test_case['product_id']
        product_name = test_case['product_name']
        expected_products = test_case['expected_similar_products']
        
        print(f"\nTest : {product_name} (ID: {product_id})")
        
        try:
            # Obtenir les recommandations
            recommendations = recommendation_engine.get_recommendations(product_id, k=10)
            
            if not recommendations:
                print("  ❌ Aucune recommandation retournée")
                continue
            
            # Vérifier les recommandations attendues
            found_expected = 0
            for expected in expected_products:
                expected_id = expected['product_id']
                expected_name = expected['product_name']
                
                # Chercher dans les recommandations
                found = any(rec['id'] == expected_id for rec in recommendations)
                
                if found:
                    found_expected += 1
                    print(f"  ✅ Trouvé : {expected_name}")
                else:
                    print(f"  ❌ Manquant : {expected_name}")
            
            # Calculer la précision
            precision = found_expected / len(expected_products) if expected_products else 0
            print(f"  Précision : {precision:.2f} ({found_expected}/{len(expected_products)})")
            
            total_tests += 1
            if precision >= 0.5:  # Seuil de 50%
                passed_tests += 1
            
        except Exception as e:
            print(f"  ❌ Erreur : {e}")
    
    print(f"\n📊 Résultat recommandations : {passed_tests}/{total_tests} tests passés")
    return passed_tests, total_tests


def test_search(test_cases):
    """Test la pertinence de la recherche sémantique."""
    print("\n🔍 TEST DE LA RECHERCHE SÉMANTIQUE")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in test_cases.get('search_queries', []):
        query = test_case['query']
        expected_products = test_case['expected_products']
        
        print(f"\nTest : '{query}'")
        
        try:
            # Effectuer la recherche
            results = search_engine.search(query, k=20)
            
            if not results:
                print("  ❌ Aucun résultat retourné")
                continue
            
            # Vérifier les résultats attendus
            found_expected = 0
            for expected in expected_products:
                expected_id = expected['product_id']
                expected_name = expected['product_name']
                min_score = expected.get('min_score', 0.5)
                
                # Chercher dans les résultats
                found_result = None
                for result in results:
                    if result['id'] == expected_id:
                        found_result = result
                        break
                
                if found_result:
                    score = found_result['search_score']
                    if score >= min_score:
                        found_expected += 1
                        print(f"  ✅ Trouvé : {expected_name} (score: {score:.3f})")
                    else:
                        print(f"  ⚠️ Trouvé mais score faible : {expected_name} (score: {score:.3f} < {min_score})")
                else:
                    print(f"  ❌ Manquant : {expected_name}")
            
            # Calculer la précision
            precision = found_expected / len(expected_products) if expected_products else 0
            print(f"  Précision : {precision:.2f} ({found_expected}/{len(expected_products)})")
            
            total_tests += 1
            if precision >= 0.5:  # Seuil de 50%
                passed_tests += 1
            
        except Exception as e:
            print(f"  ❌ Erreur : {e}")
    
    print(f"\n📊 Résultat recherche : {passed_tests}/{total_tests} tests passés")
    return passed_tests, total_tests


def test_rag(test_cases):
    """Test la qualité des réponses RAG."""
    print("\n🔍 TEST DE L'ASSISTANT RAG")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in test_cases.get('rag_questions', []):
        question = test_case['question']
        expected_keywords = test_case['expected_answer_contains']
        expected_sources = test_case['expected_sources']
        
        print(f"\nTest : '{question}'")
        
        try:
            # Poser la question
            response = rag_service.ask_question(question)
            
            if response['status'] != 'success':
                print(f"  ❌ Statut d'erreur : {response['status']}")
                continue
            
            answer = response['answer'].lower()
            sources = response['sources']
            
            # Vérifier les mots-clés attendus
            found_keywords = 0
            for keyword in expected_keywords:
                if keyword.lower() in answer:
                    found_keywords += 1
                    print(f"  ✅ Mot-clé trouvé : '{keyword}'")
                else:
                    print(f"  ❌ Mot-clé manquant : '{keyword}'")
            
            # Vérifier les sources
            found_sources = 0
            for expected_source in expected_sources:
                source_found = any(
                    expected_source in source.get('metadata', {}).get('category', '') or
                    expected_source in source.get('metadata', {}).get('type', '')
                    for source in sources
                )
                
                if source_found:
                    found_sources += 1
                    print(f"  ✅ Source trouvée : '{expected_source}'")
                else:
                    print(f"  ❌ Source manquante : '{expected_source}'")
            
            # Calculer les scores
            keyword_score = found_keywords / len(expected_keywords) if expected_keywords else 0
            source_score = found_sources / len(expected_sources) if expected_sources else 0
            overall_score = (keyword_score + source_score) / 2
            
            print(f"  Score mots-clés : {keyword_score:.2f} ({found_keywords}/{len(expected_keywords)})")
            print(f"  Score sources : {source_score:.2f} ({found_sources}/{len(expected_sources)})")
            print(f"  Score global : {overall_score:.2f}")
            
            total_tests += 1
            if overall_score >= 0.6:  # Seuil de 60%
                passed_tests += 1
            
        except Exception as e:
            print(f"  ❌ Erreur : {e}")
    
    print(f"\n📊 Résultat RAG : {passed_tests}/{total_tests} tests passés")
    return passed_tests, total_tests


def test_performance():
    """Test les performances des fonctionnalités ML."""
    print("\n⚡ TEST DES PERFORMANCES")
    print("=" * 50)
    
    # Test recommandations
    print("\nTest recommandations :")
    product = Product.objects.filter(is_active=True).first()
    if product:
        times = []
        for i in range(10):
            start_time = time.time()
            recommendations = recommendation_engine.get_recommendations(product.id, k=10)
            response_time = (time.time() - start_time) * 1000
            times.append(response_time)
        
        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        print(f"  Temps moyen : {avg_time:.2f}ms")
        print(f"  P95 : {p95_time:.2f}ms")
        print(f"  Objectif P95 ≤ 150ms : {'✅' if p95_time <= 150 else '❌'}")
    
    # Test recherche
    print("\nTest recherche :")
    times = []
    for i in range(10):
        start_time = time.time()
        results = search_engine.search("test", k=20)
        response_time = (time.time() - start_time) * 1000
        times.append(response_time)
    
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    
    print(f"  Temps moyen : {avg_time:.2f}ms")
    print(f"  P95 : {p95_time:.2f}ms")
    print(f"  Objectif P95 ≤ 300ms : {'✅' if p95_time <= 300 else '❌'}")
    
    # Test RAG
    print("\nTest RAG :")
    times = []
    for i in range(5):  # Moins de tests car plus lent
        start_time = time.time()
        response = rag_service.ask_question("Test de performance")
        response_time = (time.time() - start_time) * 1000
        times.append(response_time)
    
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    
    print(f"  Temps moyen : {avg_time:.2f}ms")
    print(f"  P95 : {p95_time:.2f}ms")
    print(f"  Objectif P95 ≤ 2000ms : {'✅' if p95_time <= 2000 else '❌'}")


def main():
    """Fonction principale de test."""
    print("🧪 TEST DE PERTINENCE - FONCTIONNALITÉS ML")
    print("=" * 60)
    
    # Charger les cas de test
    test_data = load_test_cases()
    if not test_data:
        return
    
    print(f"Version des tests : {test_data.get('version', 'N/A')}")
    print(f"Description : {test_data.get('description', 'N/A')}")
    
    # Exécuter les tests
    total_passed = 0
    total_tests = 0
    
    # Test recommandations
    rec_passed, rec_total = test_recommendations(test_data)
    total_passed += rec_passed
    total_tests += rec_total
    
    # Test recherche
    search_passed, search_total = test_search(test_data)
    total_passed += search_passed
    total_tests += search_total
    
    # Test RAG
    rag_passed, rag_total = test_rag(test_data)
    total_passed += rag_passed
    total_tests += rag_total
    
    # Test performances
    test_performance()
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 60)
    
    if total_tests > 0:
        overall_score = total_passed / total_tests
        print(f"Score global : {overall_score:.2f} ({total_passed}/{total_tests})")
        
        if overall_score >= 0.6:
            print("✅ Tests de pertinence PASSÉS")
        else:
            print("❌ Tests de pertinence ÉCHOUÉS")
    else:
        print("⚠️ Aucun test exécuté")
    
    print("\nObjectifs de performance :")
    print("- Recommandations : P95 ≤ 150ms")
    print("- Recherche : P95 ≤ 300ms")
    print("- RAG : P95 ≤ 2000ms")


if __name__ == "__main__":
    main()


