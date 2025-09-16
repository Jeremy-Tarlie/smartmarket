"""
Modèles pour l'application catalog.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser


class Category(models.Model):
    """Modèle pour les catégories de produits."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Modèle pour les produits."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Catégorie",
    )
    name = models.CharField(max_length=200, verbose_name="Nom")
    slug = models.SlugField(max_length=200, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix",
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "slug"], name="unique_product_per_category"
            ),
            models.CheckConstraint(
                check=models.Q(price__gte=0), name="price_non_negative"
            ),
        ]
        indexes = [
            models.Index(fields=["slug"], name="product_slug_idx"),
            models.Index(
                fields=["category", "is_active"], name="product_category_active_idx"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.price < 0:
            raise ValidationError({"price": "Le prix ne peut pas être négatif."})


class User(AbstractUser):
    """Modèle utilisateur personnalisé."""
    
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    is_gdpr_consent = models.BooleanField(default=False, verbose_name="Consentement RGPD")
    gdpr_consent_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de consentement RGPD")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Order(models.Model):
    """Modèle pour les commandes."""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Utilisateur"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant total"
    )
    shipping_address = models.TextField(verbose_name="Adresse de livraison")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="order_user_status_idx"),
            models.Index(fields=["created_at"], name="order_created_at_idx"),
        ]
    
    def __str__(self):
        return f"Commande #{self.id} - {self.user.email} ({self.status})"


class OrderItem(models.Model):
    """Modèle pour les éléments de commande."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Commande"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Produit"
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantité")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix unitaire"
    )
    
    class Meta:
        verbose_name = "Élément de commande"
        verbose_name_plural = "Éléments de commande"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"], name="unique_order_product"
            ),
        ]
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity} - {self.order}"
    
    @property
    def total_price(self):
        """Calcule le prix total de cet élément."""
        return self.quantity * self.unit_price
