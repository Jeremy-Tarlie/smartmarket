"""
Signaux Django pour l'invalidation du cache ML et notifications temps réel.
"""

import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Product, Category, Order
from ml.cache import ml_cache
from .tasks import send_order_email


@receiver(post_save, sender=Product)
def invalidate_product_cache_on_save(sender, instance, **kwargs):
    """
    Invalide le cache ML lorsqu'un produit est sauvegardé.
    """
    try:
        # Invalider le cache pour ce produit
        ml_cache.invalidate_product_cache(instance.id)
        
        # Invalider aussi le cache global des recommandations et recherche
        # car les embeddings peuvent avoir changé
        ml_cache.delete_pattern("recommendations:*")
        ml_cache.delete_pattern("search:*")
        
    except Exception as e:
        # Ne pas faire échouer la sauvegarde si le cache échoue
        print(f"Erreur lors de l'invalidation du cache pour le produit {instance.id}: {e}")


@receiver(post_delete, sender=Product)
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    """
    Invalide le cache ML lorsqu'un produit est supprimé.
    """
    try:
        # Invalider le cache pour ce produit
        ml_cache.invalidate_product_cache(instance.id)
        
        # Invalider aussi le cache global
        ml_cache.delete_pattern("recommendations:*")
        ml_cache.delete_pattern("search:*")
        
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache pour le produit supprimé {instance.id}: {e}")


@receiver(post_save, sender=Category)
def invalidate_category_cache_on_save(sender, instance, **kwargs):
    """
    Invalide le cache ML lorsqu'une catégorie est modifiée.
    """
    try:
        # Invalider le cache global car les catégories affectent les recommandations
        ml_cache.delete_pattern("recommendations:*")
        ml_cache.delete_pattern("search:*")
        
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache pour la catégorie {instance.id}: {e}")


@receiver(post_save, sender=Order)
def handle_order_created(sender, instance, created, **kwargs):
    """
    Gère la création d'une nouvelle commande.
    """
    if created:
        # Programmer l'envoi d'email après commit de la transaction
        transaction.on_commit(
            lambda: send_order_email.delay(instance.id)
        )
        
        # Envoyer une notification WebSocket aux admins
        transaction.on_commit(
            lambda: send_order_notification_to_admins(instance)
        )


@receiver(post_save, sender=Order)
def handle_order_updated(sender, instance, **kwargs):
    """
    Gère la mise à jour d'une commande.
    """
    # Envoyer une notification WebSocket aux admins et à l'utilisateur
    transaction.on_commit(
        lambda: send_order_update_notifications(instance)
    )


def send_order_notification_to_admins(order):
    """
    Envoie une notification de nouvelle commande aux admins.
    """
    try:
        channel_layer = get_channel_layer()
        
        order_data = {
            'id': order.id,
            'user': {
                'id': order.user.id,
                'username': order.user.username,
            },
            'product': {
                'id': order.product.id,
                'name': order.product.name,
            },
            'quantity': order.quantity,
            'total_price': str(order.total_price),
            'status': order.status,
            'created_at': order.created_at.isoformat(),
        }
        
        async_to_sync(channel_layer.group_send)(
            'admin_orders',
            {
                'type': 'order_created',
                'order': order_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Envoyer aussi une notification générale
        async_to_sync(channel_layer.group_send)(
            'admin_notifications',
            {
                'type': 'system_notification',
                'notification': {
                    'type': 'new_order',
                    'message': f'Nouvelle commande #{order.id} de {order.user.username}',
                    'order_id': order.id,
                    'user_id': order.user.id,
                },
                'timestamp': timezone.now().isoformat()
            }
        )
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de notification de commande: {e}")


def send_order_update_notifications(order):
    """
    Envoie des notifications de mise à jour de commande.
    """
    try:
        channel_layer = get_channel_layer()
        
        order_data = {
            'id': order.id,
            'user': {
                'id': order.user.id,
                'username': order.user.username,
            },
            'product': {
                'id': order.product.id,
                'name': order.product.name,
            },
            'quantity': order.quantity,
            'total_price': str(order.total_price),
            'status': order.status,
            'updated_at': timezone.now().isoformat(),
        }
        
        # Notification aux admins
        async_to_sync(channel_layer.group_send)(
            'admin_orders',
            {
                'type': 'order_updated',
                'order': order_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Notification à l'utilisateur
        async_to_sync(channel_layer.group_send)(
            f'user_{order.user.id}_notifications',
            {
                'type': 'order_status_update',
                'order': order_data,
                'timestamp': timezone.now().isoformat()
            }
        )
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de notification de mise à jour: {e}")


def send_ml_task_notification(task_name, status, result=None):
    """
    Envoie une notification de tâche ML terminée aux admins.
    """
    try:
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            'admin_notifications',
            {
                'type': 'ml_task_completed',
                'task': {
                    'name': task_name,
                    'status': status,
                    'result': result,
                },
                'timestamp': timezone.now().isoformat()
            }
        )
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de notification de tâche ML: {e}")


@receiver(post_delete, sender=Category)
def invalidate_category_cache_on_delete(sender, instance, **kwargs):
    """
    Invalide le cache ML lorsqu'une catégorie est supprimée.
    """
    try:
        # Invalider le cache de recherche
        ml_cache.delete_pattern("search:*")
        
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache pour la catégorie supprimée {instance.id}: {e}")


