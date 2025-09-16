"""
Tests pour l'application catalog.
"""

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Product


class CategoryModelTest(TestCase):
    """Tests pour le modèle Category."""

    def test_category_creation(self):
        """Test de création d'une catégorie."""
        category = Category.objects.create(name="Électronique")
        self.assertEqual(category.name, "Électronique")
        self.assertEqual(category.slug, "electronique")

    def test_category_slug_auto_generation(self):
        """Test de génération automatique du slug."""
        category = Category.objects.create(name="Vêtements & Accessoires")
        self.assertEqual(category.slug, "vetements-accessoires")

    def test_category_unique_name(self):
        """Test de l'unicité du nom de catégorie."""
        Category.objects.create(name="Test Unique")
        with self.assertRaises(ValidationError):
            Category.objects.create(name="Test Unique")


class ProductModelTest(TestCase):
    """Tests pour le modèle Product."""

    def setUp(self):
        """Configuration des tests."""
        self.category = Category.objects.create(name="Test Category")

    def test_product_creation(self):
        """Test de création d'un produit."""
        product = Product.objects.create(
            category=self.category, name="Test Product", price=19.99, stock=10
        )
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.price, 19.99)
        self.assertEqual(product.stock, 10)
        self.assertTrue(product.is_active)

    def test_product_slug_auto_generation(self):
        """Test de génération automatique du slug."""
        product = Product.objects.create(
            category=self.category, name="Test Product Name", price=19.99
        )
        self.assertEqual(product.slug, "test-product-name")

    def test_product_price_validation(self):
        """Test de validation du prix."""
        product = Product(category=self.category, name="Test Product", price=-10.00)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_unique_constraint(self):
        """Test de la contrainte d'unicité (category, slug)."""
        Product.objects.create(category=self.category, name="Test Product Unique", price=19.99)
        with self.assertRaises(ValidationError):
            Product.objects.create(
                category=self.category, name="Test Product Unique", price=29.99
            )


class ProductViewsTest(TestCase):
    """Tests pour les vues des produits."""

    def setUp(self):
        """Configuration des tests."""
        self.client = Client()
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            price=19.99,
            stock=10,
            is_active=True,
        )

    def test_product_list_view(self):
        """Test de la vue liste des produits."""
        url = reverse("catalog:product_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertContains(response, "19.99")

    def test_product_detail_view(self):
        """Test de la vue détail d'un produit."""
        url = reverse("catalog:product_detail", kwargs={"slug": self.product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertContains(response, "Test Category")

    def test_product_detail_view_404(self):
        """Test de la vue détail avec un slug inexistant."""
        url = reverse("catalog:product_detail", kwargs={"slug": "inexistant"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_inactive_product_not_visible(self):
        """Test que les produits inactifs ne sont pas visibles."""
        self.product.is_active = False
        self.product.save()

        url = reverse("catalog:product_list")
        response = self.client.get(url)
        self.assertNotContains(response, "Test Product")

        url = reverse("catalog:product_detail", kwargs={"slug": self.product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
