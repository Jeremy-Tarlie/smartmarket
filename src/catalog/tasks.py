"""
Tâches Celery pour SmartMarket.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Product, Order, User
from ml.cache import ml_cache
from ml.manifest import ml_manifest
from .signals import send_ml_task_notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def rebuild_ml_indexes(self, force: bool = False) -> Dict[str, Any]:
    """
    Reconstruit les index ML (embeddings et recommandations).
    
    Args:
        force: Force la reconstruction même si les index sont récents
        
    Returns:
        Résultat de la reconstruction
    """
    task_id = self.request.id
    logger.info(f"Starting ML index rebuild - Task ID: {task_id}")
    
    try:
        # Vérifier si une reconstruction récente existe
        if not force:
            last_rebuild = ml_cache.get('last_ml_rebuild')
            if last_rebuild and (timezone.now() - last_rebuild).seconds < 1800:  # 30 minutes
                logger.info("ML indexes are recent, skipping rebuild")
                return {
                    'status': 'skipped',
                    'reason': 'Recent rebuild exists',
                    'last_rebuild': last_rebuild.isoformat()
                }
        
        # Importer ici pour éviter les imports circulaires
        from ml.vectorization import ProductVectorizer
        from ml.search import SemanticSearchEngine
        
        start_time = time.time()
        
        # Obtenir les produits actifs
        products = Product.objects.filter(is_active=True)
        product_count = products.count()
        
        if product_count == 0:
            logger.warning("No active products found for ML index rebuild")
            return {
                'status': 'warning',
                'message': 'No active products found',
                'product_count': 0
            }
        
        logger.info(f"Rebuilding ML indexes for {product_count} products")
        
        # Reconstruire les embeddings
        vectorizer = ProductVectorizer()
        vectorizer.fit_tfidf(products)
        embeddings = vectorizer.get_embeddings(products)
        vectorizer.save_embeddings(embeddings)
        
        # Reconstruire l'index de recherche
        search_engine = SemanticSearchEngine()
        search_engine.load_embedding_model(vectorizer.embedding_model)
        search_engine.build_index(embeddings, vectorizer.product_ids)
        
        # Mettre à jour le manifest
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
        
        # Invalider le cache ML
        ml_cache.invalidate_all_cache()
        ml_cache.set('last_ml_rebuild', timezone.now(), ttl=3600)
        
        execution_time = time.time() - start_time
        
        logger.info(f"ML index rebuild completed in {execution_time:.2f}s")
        
        # Envoyer une notification WebSocket
        send_ml_task_notification(
            'rebuild_ml_indexes',
            'success',
            {
                'product_count': product_count,
                'execution_time': execution_time
            }
        )
        
        return {
            'status': 'success',
            'product_count': product_count,
            'execution_time': execution_time,
            'task_id': task_id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML index rebuild failed: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 30})
def send_order_email(self, order_id: int) -> Dict[str, Any]:
    """
    Envoie un email de confirmation de commande.
    
    Args:
        order_id: ID de la commande
        
    Returns:
        Résultat de l'envoi
    """
    task_id = self.request.id
    logger.info(f"Sending order email - Order ID: {order_id}, Task ID: {task_id}")
    
    try:
        # Récupérer la commande
        order = Order.objects.select_related('user', 'product').get(id=order_id)
        
        # Préparer le contenu de l'email
        subject = f"Confirmation de commande #{order.id}"
        message = f"""
        Bonjour {order.user.username},
        
        Votre commande a été confirmée avec succès !
        
        Détails de la commande :
        - Numéro : #{order.id}
        - Produit : {order.product.name}
        - Quantité : {order.quantity}
        - Prix total : {order.total_price}€
        - Date : {order.created_at.strftime('%d/%m/%Y %H:%M')}
        
        Merci pour votre achat !
        
        L'équipe SmartMarket
        """
        
        # Envoyer l'email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
        
        logger.info(f"Order email sent successfully - Order ID: {order_id}")
        
        return {
            'status': 'success',
            'order_id': order_id,
            'recipient': order.user.email,
            'task_id': task_id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Order.DoesNotExist:
        logger.error(f"Order not found - Order ID: {order_id}")
        return {
            'status': 'error',
            'error': 'Order not found',
            'order_id': order_id
        }
    except Exception as e:
        logger.error(f"Failed to send order email: {e}")
        raise self.retry(exc=e, countdown=30)


@shared_task(bind=True)
def purge_cache(self, cache_type: str = 'all') -> Dict[str, Any]:
    """
    Purge le cache selon le type spécifié.
    
    Args:
        cache_type: Type de cache à purger ('all', 'ml', 'recommendations', 'search')
        
    Returns:
        Résultat de la purge
    """
    task_id = self.request.id
    logger.info(f"Purging cache - Type: {cache_type}, Task ID: {task_id}")
    
    try:
        start_time = time.time()
        
        if cache_type == 'all':
            ml_cache.invalidate_all_cache()
            purged_count = "all"
        elif cache_type == 'ml':
            ml_cache.delete_pattern("recommendations:*")
            ml_cache.delete_pattern("search:*")
            ml_cache.delete_pattern("product_embedding:*")
            purged_count = "ml_patterns"
        elif cache_type == 'recommendations':
            ml_cache.delete_pattern("recommendations:*")
            purged_count = "recommendations"
        elif cache_type == 'search':
            ml_cache.delete_pattern("search:*")
            purged_count = "search"
        else:
            return {
                'status': 'error',
                'error': f'Invalid cache type: {cache_type}',
                'task_id': task_id
            }
        
        execution_time = time.time() - start_time
        
        logger.info(f"Cache purge completed in {execution_time:.2f}s")
        
        return {
            'status': 'success',
            'cache_type': cache_type,
            'purged_count': purged_count,
            'execution_time': execution_time,
            'task_id': task_id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache purge failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'task_id': task_id
        }


@shared_task(bind=True)
def generate_daily_report(self) -> Dict[str, Any]:
    """
    Génère un rapport quotidien des statistiques.
    
    Returns:
        Rapport quotidien
    """
    task_id = self.request.id
    logger.info(f"Generating daily report - Task ID: {task_id}")
    
    try:
        # Calculer les statistiques
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Commandes d'hier
        orders_yesterday = Order.objects.filter(
            created_at__date=yesterday
        ).count()
        
        # Revenus d'hier
        revenue_yesterday = Order.objects.filter(
            created_at__date=yesterday
        ).aggregate(
            total=models.Sum('total_price')
        )['total'] or 0
        
        # Produits les plus vendus
        top_products = Order.objects.filter(
            created_at__date=yesterday
        ).values('product__name').annotate(
            total_quantity=models.Sum('quantity')
        ).order_by('-total_quantity')[:5]
        
        # Nouveaux utilisateurs
        new_users = User.objects.filter(
            date_joined__date=yesterday
        ).count()
        
        report_data = {
            'date': yesterday.isoformat(),
            'orders_count': orders_yesterday,
            'revenue': float(revenue_yesterday),
            'new_users': new_users,
            'top_products': list(top_products),
            'generated_at': timezone.now().isoformat(),
            'task_id': task_id
        }
        
        # Sauvegarder le rapport (optionnel)
        ml_cache.set(f'daily_report_{yesterday}', report_data, ttl=86400 * 7)  # 7 jours
        
        logger.info(f"Daily report generated successfully")
        
        return {
            'status': 'success',
            'report': report_data
        }
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'task_id': task_id
        }


@shared_task(bind=True)
def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
    """
    Nettoie les anciennes données (logs, cache, etc.).
    
    Args:
        days: Nombre de jours de rétention
        
    Returns:
        Résultat du nettoyage
    """
    task_id = self.request.id
    logger.info(f"Cleaning up old data - Days: {days}, Task ID: {task_id}")
    
    try:
        start_time = time.time()
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Nettoyer les anciens rapports
        old_reports = ml_cache.delete_pattern(f'daily_report_*')
        
        # Nettoyer les anciens logs de tâches (si stockés en cache)
        old_logs = ml_cache.delete_pattern(f'task_log_*')
        
        execution_time = time.time() - start_time
        
        logger.info(f"Data cleanup completed in {execution_time:.2f}s")
        
        return {
            'status': 'success',
            'days_retention': days,
            'cutoff_date': cutoff_date.isoformat(),
            'execution_time': execution_time,
            'task_id': task_id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'task_id': task_id
        }
