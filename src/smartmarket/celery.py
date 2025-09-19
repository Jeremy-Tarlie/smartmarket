"""
Configuration Celery pour SmartMarket.
"""

import os
from celery import Celery
from django.conf import settings

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartmarket.settings.prod')

app = Celery('smartmarket')

# Configuration depuis Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches
app.autodiscover_tasks()

# Configuration des files d'attente
app.conf.update(
    # Broker Redis
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    
    # Files d'attente séparées
    task_routes={
        'catalog.tasks.rebuild_ml_indexes': {'queue': 'ml'},
        'catalog.tasks.send_order_email': {'queue': 'emails'},
        'catalog.tasks.purge_cache': {'queue': 'maintenance'},
        'catalog.tasks.generate_report': {'queue': 'reports'},
    },
    
    # Configuration des workers
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Retry et backoff
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # 10 minutes max
    
    # Timeouts
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    
    # Sérialisation
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Beat scheduler
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Sécurité
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    'rebuild-ml-indexes': {
        'task': 'catalog.tasks.rebuild_ml_indexes',
        'schedule': 3600.0,  # Toutes les heures
        'options': {
            'queue': 'ml',
            'expires': 300,  # Expire après 5 minutes si pas pris
        }
    },
    'purge-cache': {
        'task': 'catalog.tasks.purge_cache',
        'schedule': 1800.0,  # Toutes les 30 minutes
        'options': {
            'queue': 'maintenance',
            'expires': 60,
        }
    },
    'daily-report': {
        'task': 'catalog.tasks.generate_daily_report',
        'schedule': 86400.0,  # Tous les jours à minuit
        'options': {
            'queue': 'reports',
            'expires': 3600,
        }
    },
}

# Configuration des limites de taux
app.conf.task_annotations = {
    'catalog.tasks.send_order_email': {'rate_limit': '10/m'},  # 10 emails par minute
    'catalog.tasks.rebuild_ml_indexes': {'rate_limit': '1/h'},  # 1 fois par heure max
    'catalog.tasks.purge_cache': {'rate_limit': '2/m'},  # 2 purges par minute max
}

@app.task(bind=True)
def debug_task(self):
    """Tâche de debug pour tester Celery."""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'

