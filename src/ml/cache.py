"""
Gestion du cache Redis pour les fonctionnalités ML.
"""

import json
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

import redis
from django.conf import settings

from .config import CACHE_TTL, CACHE_PREFIX


class MLCache:
    """Gestionnaire de cache pour les fonctionnalités ML."""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Établit la connexion Redis."""
        try:
            # Configuration Redis depuis Django settings
            redis_config = getattr(settings, 'REDIS_CONFIG', {})
            
            self.redis_client = redis.Redis(
                host=redis_config.get('HOST', 'localhost'),
                port=redis_config.get('PORT', 6379),
                db=redis_config.get('DB', 0),
                decode_responses=True
            )
            
            # Test de connexion
            self.redis_client.ping()
            
        except Exception as e:
            print(f"Erreur de connexion Redis: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Génère une clé de cache unique.
        
        Args:
            prefix: Préfixe de la clé
            **kwargs: Paramètres pour la clé
            
        Returns:
            Clé de cache
        """
        # Créer un hash des paramètres
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        return f"{CACHE_PREFIX}:{prefix}:{params_hash}"
    
    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            prefix: Préfixe de la clé
            **kwargs: Paramètres pour la clé
            
        Returns:
            Valeur en cache ou None
        """
        if not self.redis_client:
            return None
        
        try:
            key = self._generate_cache_key(prefix, **kwargs)
            value = self.redis_client.get(key)
            
            if value:
                return json.loads(value)
            
        except Exception as e:
            print(f"Erreur lors de la récupération du cache: {e}")
        
        return None
    
    def set(self, prefix: str, value: Any, ttl: int = CACHE_TTL, **kwargs):
        """
        Stocke une valeur dans le cache.
        
        Args:
            prefix: Préfixe de la clé
            value: Valeur à stocker
            ttl: Time to live en secondes
            **kwargs: Paramètres pour la clé
        """
        if not self.redis_client:
            return
        
        try:
            key = self._generate_cache_key(prefix, **kwargs)
            serialized_value = json.dumps(value, default=str)
            
            self.redis_client.setex(key, ttl, serialized_value)
            
        except Exception as e:
            print(f"Erreur lors du stockage en cache: {e}")
    
    def delete(self, prefix: str, **kwargs):
        """
        Supprime une valeur du cache.
        
        Args:
            prefix: Préfixe de la clé
            **kwargs: Paramètres pour la clé
        """
        if not self.redis_client:
            return
        
        try:
            key = self._generate_cache_key(prefix, **kwargs)
            self.redis_client.delete(key)
            
        except Exception as e:
            print(f"Erreur lors de la suppression du cache: {e}")
    
    def delete_pattern(self, pattern: str):
        """
        Supprime toutes les clés correspondant à un pattern.
        
        Args:
            pattern: Pattern des clés à supprimer
        """
        if not self.redis_client:
            return
        
        try:
            full_pattern = f"{CACHE_PREFIX}:{pattern}"
            keys = self.redis_client.keys(full_pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                
        except Exception as e:
            print(f"Erreur lors de la suppression par pattern: {e}")
    
    def invalidate_product_cache(self, product_id: int):
        """
        Invalide le cache pour un produit spécifique.
        
        Args:
            product_id: ID du produit
        """
        # Invalider les recommandations
        self.delete_pattern(f"recommendations:*product_id={product_id}*")
        
        # Invalider les embeddings du produit
        self.delete_pattern(f"product_embedding:*product_id={product_id}*")
    
    def invalidate_all_cache(self):
        """Invalide tout le cache ML."""
        if not self.redis_client:
            return
        
        try:
            pattern = f"{CACHE_PREFIX}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                
        except Exception as e:
            print(f"Erreur lors de l'invalidation complète du cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = self.redis_client.info()
            
            # Compter les clés ML
            ml_keys = self.redis_client.keys(f"{CACHE_PREFIX}:*")
            
            return {
                "status": "connected",
                "total_keys": info.get("db0", {}).get("keys", 0),
                "ml_keys": len(ml_keys),
                "memory_usage": info.get("used_memory_human", "N/A"),
                "uptime": info.get("uptime_in_seconds", 0),
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Instance globale du cache
ml_cache = MLCache()

