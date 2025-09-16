"""
Filtres pour l'API REST.
"""

import django_filters
from django.db.models import Q

from .models import Product, Order


class ProductFilter(django_filters.FilterSet):
    """
    Filtres pour les produits.
    """
    
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Product
        fields = ['category', 'category_name', 'min_price', 'max_price', 'is_active', 'in_stock', 'search']
    
    def filter_in_stock(self, queryset, name, value):
        """Filtre les produits en stock ou non."""
        if value is True:
            return queryset.filter(stock__gt=0)
        elif value is False:
            return queryset.filter(stock=0)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Recherche dans le nom et la description des produits."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) | 
                Q(description__icontains=value)
            )
        return queryset


class OrderFilter(django_filters.FilterSet):
    """
    Filtres pour les commandes.
    """
    
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    min_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    user_email = django_filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Order
        fields = [
            'status', 'min_amount', 'max_amount', 
            'user_email', 'created_after', 'created_before'
        ]
