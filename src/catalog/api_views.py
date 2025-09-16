"""
Vues API REST pour l'application catalog.
"""

import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters, throttling
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import Category, Product, Order
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    UserGDPRExportSerializer,
)
from .permissions import (
    ReadOnlyOrManagerOrAdmin,
    IsOwnerOrAdmin,
    IsManagerOrAdmin,
    IsClientOrManagerOrAdmin,
    SensitiveEndpointPermission,
)
from .filters import ProductFilter, OrderFilter

User = get_user_model()
logger = logging.getLogger(__name__)


class SensitiveEndpointThrottle(UserRateThrottle):
    """Throttling pour les endpoints sensibles."""
    scope = 'sensitive'


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les catégories (lecture seule).
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les produits.
    """
    queryset = Product.objects.select_related('category').all()
    permission_classes = [ReadOnlyOrManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at', 'stock']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        """Retourne le queryset approprié selon les permissions."""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les commandes.
    """
    permission_classes = [IsClientOrManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    throttle_classes = [SensitiveEndpointThrottle]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action."""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderDetailSerializer
    
    def get_queryset(self):
        """Retourne le queryset approprié selon les permissions."""
        queryset = Order.objects.select_related('user').prefetch_related('items__product')
        
        if not self.request.user.is_staff and not self.request.user.groups.filter(name='manager').exists():
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Crée une nouvelle commande."""
        serializer.save(user=self.request.user)
        
        logger.info(
            f"Commande créée par l'utilisateur {self.request.user.email}",
            extra={
                'user_id': self.request.user.id,
                'action': 'order_created',
                'timestamp': timezone.now().isoformat()
            }
        )
    
    def perform_update(self, serializer):
        """Met à jour une commande."""
        old_status = self.get_object().status
        serializer.save()
        new_status = serializer.instance.status
        
        logger.info(
            f"Commande {serializer.instance.id} mise à jour par {self.request.user.email}",
            extra={
                'user_id': self.request.user.id,
                'order_id': serializer.instance.id,
                'old_status': old_status,
                'new_status': new_status,
                'action': 'order_updated',
                'timestamp': timezone.now().isoformat()
            }
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les utilisateurs (lecture seule).
    """
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['username']
    
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[SensitiveEndpointPermission],
        throttle_classes=[SensitiveEndpointThrottle],
        url_path='export-gdpr'
    )
    def export_gdpr(self, request, pk=None):
        """
        Export des données RGPD pour un utilisateur.
        """
        user = self.get_object()
        
        if not request.user.is_staff and user != request.user:
            return Response(
                {'error': 'Accès non autorisé aux données de cet utilisateur.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserGDPRExportSerializer(user)
        
        logger.info(
            f"Export RGPD demandé pour l'utilisateur {user.email} par {request.user.email}",
            extra={
                'requested_user_id': user.id,
                'requester_user_id': request.user.id,
                'action': 'gdpr_export',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[SensitiveEndpointPermission],
        throttle_classes=[SensitiveEndpointThrottle],
        url_path='delete-gdpr'
    )
    def delete_gdpr(self, request, pk=None):
        """
        Suppression des données RGPD pour un utilisateur.
        """
        user = self.get_object()
        
        if not request.user.is_staff and user != request.user:
            return Response(
                {'error': 'Accès non autorisé pour supprimer les données de cet utilisateur.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            user.is_active = False
            user.save()
            
            orders = user.orders.all()
            for order in orders:
                order.shipping_address = "[SUPPRIMÉ]"
                order.notes = "[SUPPRIMÉ]"
                order.save()
            
            user.first_name = "[SUPPRIMÉ]"
            user.last_name = "[SUPPRIMÉ]"
            user.phone = ""
            user.address = ""
            user.email = f"deleted_{user.id}@example.com"
            user.username = f"deleted_{user.id}"
            user.save()
        
        logger.info(
            f"Suppression RGPD effectuée pour l'utilisateur {user.id} par {request.user.email}",
            extra={
                'deleted_user_id': user.id,
                'requester_user_id': request.user.id,
                'action': 'gdpr_deletion',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        return Response(
            {
                'message': 'Données utilisateur supprimées avec succès.',
                'user_id': user.id,
                'deletion_date': timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
