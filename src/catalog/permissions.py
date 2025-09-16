"""
Permissions personnalisées pour l'API REST.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre seulement aux propriétaires
    d'un objet de le modifier.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission pour permettre l'accès seulement au propriétaire ou aux admins.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        return obj.user == request.user


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission pour les managers et admins.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.groups.filter(name='manager').exists())
        )


class IsClientOrManagerOrAdmin(permissions.BasePermission):
    """
    Permission pour les clients, managers et admins.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_staff or request.user.groups.filter(name='manager').exists():
            return True
        
        return request.user.groups.filter(name='client').exists()


class ReadOnlyOrManagerOrAdmin(permissions.BasePermission):
    """
    Permission en lecture seule pour tous, écriture pour managers et admins.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.groups.filter(name='manager').exists())
        )


class SensitiveEndpointPermission(permissions.BasePermission):
    """
    Permission pour les endpoints sensibles (export RGPD, suppression, etc.).
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_staff:
            return True
        
        if hasattr(view, 'get_object'):
            obj = view.get_object()
            return obj == request.user
        
        return False
