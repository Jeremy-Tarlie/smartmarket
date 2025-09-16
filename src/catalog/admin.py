"""
Configuration de l'administration Django pour l'application catalog.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Administration des catégories."""

    list_display = ["name", "slug", "product_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    def product_count(self, obj):
        """Affiche le nombre de produits dans cette catégorie."""
        return obj.products.count()

    product_count.short_description = "Nombre de produits"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Administration des produits."""

    list_display = [
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "created_at",
        "formatted_price",
    ]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["category"]
    readonly_fields = ["created_at", "updated_at"]
    list_select_related = ["category"]

    fieldsets = (
        (
            "Informations générales",
            {"fields": ("name", "slug", "category", "description")},
        ),
        ("Prix et stock", {"fields": ("price", "stock")}),
        ("Statut", {"fields": ("is_active",)}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["activate_products", "deactivate_products"]

    def get_queryset(self, request):
        """Optimise les requêtes avec select_related."""
        return super().get_queryset(request).select_related("category")

    def formatted_price(self, obj):
        """Affiche le prix formaté avec couleur selon le stock."""
        if obj.stock == 0:
            color = "red"
        elif obj.stock < 10:
            color = "orange"
        else:
            color = "green"

        return format_html('<span style="color: {};">{:.2f} €</span>', color, obj.price)

    formatted_price.short_description = "Prix"

    def activate_products(self, request, queryset):
        """Action pour activer les produits sélectionnés."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} produit(s) activé(s) avec succès.")

    activate_products.short_description = "Activer les produits sélectionnés"

    def deactivate_products(self, request, queryset):
        """Action pour désactiver les produits sélectionnés."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} produit(s) désactivé(s) avec succès.")

    deactivate_products.short_description = "Désactiver les produits sélectionnés"
