"""
Signaux Django pour l'invalidation du cache ML.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Category
from ml.cache import ml_cache


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
        # Invalider le cache de recherche car les catégories sont utilisées dans les filtres
        ml_cache.delete_pattern("search:*")
        
    except Exception as e:
        print(f"Erreur lors de l'invalidation du cache pour la catégorie {instance.id}: {e}")


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

