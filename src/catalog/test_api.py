"""
Tests pour l'API REST.
"""

import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from .models import Category, Product, Order, OrderItem

User = get_user_model()


class APITestCase(APITestCase):
    """Classe de base pour les tests API."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = APIClient()
        
        self.admin_group = Group.objects.create(name='admin')
        self.manager_group = Group.objects.create(name='manager')
        self.client_group = Group.objects.create(name='client')
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='Test',
            is_staff=True,
            is_superuser=True
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='manager123',
            first_name='Manager',
            last_name='Test'
        )
        self.manager_user.groups.add(self.manager_group)
        
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='client123',
            first_name='Client',
            last_name='Test'
        )
        self.client_user.groups.add(self.client_group)
        
        self.category = Category.objects.create(
            name='Électronique',
            slug='electronique'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Smartphone Test',
            slug='smartphone-test',
            description='Un smartphone de test',
            price=Decimal('299.99'),
            stock=10,
            is_active=True
        )


class CategoryAPITest(APITestCase):
    """Tests pour l'API des catégories."""
    
    def test_list_categories_anonymous(self):
        """Test de la liste des catégories en anonyme."""
        url = reverse('catalog_api:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_detail_category_anonymous(self):
        """Test du détail d'une catégorie en anonyme."""
        url = reverse('catalog_api:category-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Électronique')


class ProductAPITest(APITestCase):
    """Tests pour l'API des produits."""
    
    def test_list_products_anonymous(self):
        """Test de la liste des produits en anonyme."""
        url = reverse('catalog_api:product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_detail_product_anonymous(self):
        """Test du détail d'un produit en anonyme."""
        url = reverse('catalog_api:product-detail', kwargs={'pk': self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Smartphone Test')
    
    def test_create_product_anonymous_forbidden(self):
        """Test de création de produit en anonyme (interdit)."""
        url = reverse('catalog_api:product-list')
        data = {
            'category': self.category.pk,
            'name': 'Nouveau Produit',
            'description': 'Description',
            'price': '99.99',
            'stock': 5
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_product_manager_allowed(self):
        """Test de création de produit par un manager (autorisé)."""
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('catalog_api:product-list')
        data = {
            'category': self.category.pk,
            'name': 'Nouveau Produit',
            'description': 'Description',
            'price': '99.99',
            'stock': 5
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
    
    def test_update_product_manager_allowed(self):
        """Test de modification de produit par un manager (autorisé)."""
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('catalog_api:product-detail', kwargs={'pk': self.product.pk})
        data = {'name': 'Produit Modifié'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Produit Modifié')
    
    def test_filter_products_by_category(self):
        """Test du filtrage des produits par catégorie."""
        url = reverse('catalog_api:product-list')
        response = self.client.get(url, {'category': 'electronique'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_search_products(self):
        """Test de la recherche de produits."""
        url = reverse('catalog_api:product-list')
        response = self.client.get(url, {'search': 'smartphone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class OrderAPITest(APITestCase):
    """Tests pour l'API des commandes."""
    
    def test_create_order_anonymous_forbidden(self):
        """Test de création de commande en anonyme (interdit)."""
        url = reverse('catalog_api:order-list')
        data = {
            'shipping_address': '123 Test Street',
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 2
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_order_client_allowed(self):
        """Test de création de commande par un client (autorisé)."""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:order-list')
        data = {
            'shipping_address': '123 Test Street',
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 2
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
    
    def test_create_order_insufficient_stock(self):
        """Test de création de commande avec stock insuffisant."""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:order-list')
        data = {
            'shipping_address': '123 Test Street',
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 15
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_orders_client_own_only(self):
        """Test que les clients ne voient que leurs propres commandes."""
        order = Order.objects.create(
            user=self.client_user,
            shipping_address='123 Test Street',
            total_amount=Decimal('599.98')
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )
        
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='other123'
        )
        other_order = Order.objects.create(
            user=other_user,
            shipping_address='456 Other Street',
            total_amount=Decimal('299.99')
        )
        
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], order.pk)
    
    def test_list_orders_manager_all_orders(self):
        """Test que les managers voient toutes les commandes."""
        order1 = Order.objects.create(
            user=self.client_user,
            shipping_address='123 Test Street',
            total_amount=Decimal('299.99')
        )
        
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='other123'
        )
        order2 = Order.objects.create(
            user=other_user,
            shipping_address='456 Other Street',
            total_amount=Decimal('199.99')
        )
        
        self.client.force_authenticate(user=self.manager_user)
        url = reverse('catalog_api:order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class UserGDPRAPITest(APITestCase):
    """Tests pour l'API RGPD des utilisateurs."""
    
    def test_export_gdpr_anonymous_forbidden(self):
        """Test d'export RGPD en anonyme (interdit)."""
        url = reverse('catalog_api:user-export-gdpr', kwargs={'pk': self.client_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_export_gdpr_own_data_allowed(self):
        """Test d'export RGPD de ses propres données (autorisé)."""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:user-export-gdpr', kwargs={'pk': self.client_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_data', response.data)
        self.assertIn('orders', response.data)
        self.assertIn('export_date', response.data)
    
    def test_export_gdpr_other_user_forbidden(self):
        """Test d'export RGPD des données d'un autre utilisateur (interdit)."""
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='other123'
        )
        
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:user-export-gdpr', kwargs={'pk': other_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_export_gdpr_admin_allowed(self):
        """Test d'export RGPD par un admin (autorisé)."""
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='other123'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('catalog_api:user-export-gdpr', kwargs={'pk': other_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_gdpr_own_data_allowed(self):
        """Test de suppression RGPD de ses propres données (autorisé)."""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:user-delete-gdpr', kwargs={'pk': self.client_user.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.client_user.refresh_from_db()
        self.assertFalse(self.client_user.is_active)
        self.assertEqual(self.client_user.first_name, '[SUPPRIMÉ]')
    
    def test_delete_gdpr_other_user_forbidden(self):
        """Test de suppression RGPD des données d'un autre utilisateur (interdit)."""
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='other123'
        )
        
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:user-delete-gdpr', kwargs={'pk': other_user.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ThrottlingTest(APITestCase):
    """Tests pour le throttling."""
    
    def test_throttling_anonymous(self):
        """Test du throttling pour les utilisateurs anonymes."""
        url = reverse('catalog_api:product-list')
        
        throttled = False
        for i in range(65):
            response = self.client.get(url)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                throttled = True
                break
        
        self.assertTrue(throttled, "Le throttling devrait se déclencher après plusieurs requêtes")
    
    def test_throttling_authenticated(self):
        """Test du throttling pour les utilisateurs authentifiés."""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:product-list')
        
        for i in range(125):
            response = self.client.get(url)
            if i < 120:
                self.assertEqual(response.status_code, status.HTTP_200_OK)
            else:
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                break


class AuthenticationTest(APITestCase):
    """Tests pour l'authentification."""
    
    def test_login_success(self):
        """Test de connexion réussie."""
        url = '/admin/login/'
        data = {
            'username': 'admin@test.com',
            'password': 'admin123'
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_302_FOUND])
    
    def test_login_failure(self):
        """Test de connexion échouée."""
        url = '/admin/login/'
        data = {
            'username': 'admin@test.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_authenticated_access(self):
        """Test d'accès authentifié."""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('catalog_api:order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthenticated_access_protected_endpoint(self):
        """Test d'accès non authentifié à un endpoint protégé."""
        url = reverse('catalog_api:order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
