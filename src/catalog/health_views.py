"""
Vues de health check pour SmartMarket.
"""

import time
import logging
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def health_live(request):
    """
    Health check simple - vérifie que l'application répond.
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'smartmarket-web'
    })


def health_ready(request):
    """
    Health check complet - vérifie toutes les dépendances.
    """
    checks = {
        'database': False,
        'redis': False,
        'channels': False,
        'celery': False,
    }
    
    errors = []
    
    # Vérification de la base de données
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = True
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
        logger.error(f"Database health check failed: {e}")
    
    # Vérification de Redis
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['redis'] = True
    except Exception as e:
        errors.append(f"Redis error: {str(e)}")
        logger.error(f"Redis health check failed: {e}")
    
    # Vérification de Channels
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            # Test simple de connexion
            async_to_sync(channel_layer.group_send)('health_check', {
                'type': 'health_check',
                'message': 'test'
            })
            checks['channels'] = True
    except Exception as e:
        errors.append(f"Channels error: {str(e)}")
        logger.error(f"Channels health check failed: {e}")
    
    # Vérification de Celery (optionnelle)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            checks['celery'] = True
    except Exception as e:
        # Celery peut ne pas être disponible, ce n'est pas critique
        logger.warning(f"Celery health check failed: {e}")
    
    # Déterminer le statut global
    critical_checks = ['database', 'redis']
    all_critical_healthy = all(checks[check] for check in critical_checks)
    
    if all_critical_healthy:
        status = 'healthy'
        status_code = 200
    else:
        status = 'unhealthy'
        status_code = 503
    
    response_data = {
        'status': status,
        'timestamp': time.time(),
        'service': 'smartmarket-web',
        'checks': checks,
        'errors': errors,
        'version': getattr(settings, 'VERSION', 'unknown'),
        'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
    }
    
    return JsonResponse(response_data, status=status_code)


def health_detailed(request):
    """
    Health check détaillé avec métriques.
    """
    try:
        # Métriques de base de données
        db_metrics = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                db_metrics['version'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT count(*) FROM catalog_product")
                db_metrics['product_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT count(*) FROM catalog_order")
                db_metrics['order_count'] = cursor.fetchone()[0]
        except Exception as e:
            db_metrics['error'] = str(e)
        
        # Métriques Redis
        redis_metrics = {}
        try:
            redis_config = getattr(settings, 'REDIS_CONFIG', {})
            redis_metrics['host'] = redis_config.get('HOST', 'unknown')
            redis_metrics['port'] = redis_config.get('PORT', 'unknown')
            redis_metrics['db'] = redis_config.get('DB', 'unknown')
        except Exception as e:
            redis_metrics['error'] = str(e)
        
        # Métriques Celery
        celery_metrics = {}
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            
            # Statistiques des workers
            stats = inspect.stats()
            if stats:
                celery_metrics['active_workers'] = len(stats)
                celery_metrics['workers'] = list(stats.keys())
            
            # Tâches actives
            active = inspect.active()
            if active:
                total_active = sum(len(tasks) for tasks in active.values())
                celery_metrics['active_tasks'] = total_active
            
            # Tâches planifiées
            scheduled = inspect.scheduled()
            if scheduled:
                total_scheduled = sum(len(tasks) for tasks in scheduled.values())
                celery_metrics['scheduled_tasks'] = total_scheduled
                
        except Exception as e:
            celery_metrics['error'] = str(e)
        
        # Métriques système
        import psutil
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }
        
        response_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'service': 'smartmarket-web',
            'metrics': {
                'database': db_metrics,
                'redis': redis_metrics,
                'celery': celery_metrics,
                'system': system_metrics,
            },
            'version': getattr(settings, 'VERSION', 'unknown'),
            'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time(),
        }, status=500)

