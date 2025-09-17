"""
URLs pour l'API REST.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import CategoryViewSet, ProductViewSet, OrderViewSet, UserViewSet
from .ml_views import (
    product_recommendations,
    semantic_search,
    rag_assistant,
    ml_status
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'users', UserViewSet, basename='user')

app_name = 'catalog_api'

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints ML
    path('products/<int:product_id>/recommendations/', product_recommendations, name='product_recommendations'),
    path('search/', semantic_search, name='semantic_search'),
    path('assistant/ask/', rag_assistant, name='rag_assistant'),
    path('ml/status/', ml_status, name='ml_status'),
]
