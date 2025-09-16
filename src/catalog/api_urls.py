"""
URLs pour l'API REST.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import CategoryViewSet, ProductViewSet, OrderViewSet, UserViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'users', UserViewSet, basename='user')

app_name = 'catalog_api'

urlpatterns = [
    path('', include(router.urls)),
]
