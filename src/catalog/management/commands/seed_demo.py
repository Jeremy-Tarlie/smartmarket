"""
Commande pour charger les données de démonstration.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Charge les données de démonstration"

    def handle(self, *args, **options):
        """Exécute la commande."""
        self.stdout.write("Chargement des données de démonstration...")

        with transaction.atomic():
            categories_data = [
                {"name": "Électronique", "slug": "electronique"},
                {"name": "Vêtements", "slug": "vetements"},
                {"name": "Maison & Jardin", "slug": "maison-jardin"},
                {"name": "Sports & Loisirs", "slug": "sports-loisirs"},
                {"name": "Livres", "slug": "livres"},
            ]

            categories = {}
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    slug=cat_data["slug"], defaults={"name": cat_data["name"]}
                )
                categories[cat_data["slug"]] = category
                if created:
                    self.stdout.write(f"  ✓ Catégorie créée: {category.name}")

            products_data = [
                {
                    "category": "electronique",
                    "name": "Smartphone Samsung Galaxy S24",
                    "description": "Smartphone haut de gamme avec écran AMOLED 6.2 pouces, 128GB de stockage.",
                    "price": 899.99,
                    "stock": 15,
                },
                {
                    "category": "electronique",
                    "name": "MacBook Air M2",
                    "description": "Ordinateur portable Apple avec processeur M2, 8GB RAM, 256GB SSD.",
                    "price": 1299.99,
                    "stock": 8,
                },
                {
                    "category": "electronique",
                    "name": "Écouteurs AirPods Pro",
                    "description": "Écouteurs sans fil avec réduction de bruit active.",
                    "price": 249.99,
                    "stock": 25,
                },
                {
                    "category": "vetements",
                    "name": "T-shirt en coton bio",
                    "description": "T-shirt confortable en coton biologique, disponible en plusieurs couleurs.",
                    "price": 24.99,
                    "stock": 50,
                },
                {
                    "category": "vetements",
                    "name": "Jean slim délavé",
                    "description": "Jean coupe slim en denim délavé, taille ajustable.",
                    "price": 79.99,
                    "stock": 30,
                },
                {
                    "category": "maison-jardin",
                    "name": "Aspirateur robot intelligent",
                    "description": "Aspirateur robot avec cartographie et programmation via smartphone.",
                    "price": 399.99,
                    "stock": 12,
                },
                {
                    "category": "maison-jardin",
                    "name": "Plante verte Monstera",
                    "description": "Plante d'intérieur Monstera deliciosa, pot en céramique inclus.",
                    "price": 45.99,
                    "stock": 20,
                },
                {
                    "category": "sports-loisirs",
                    "name": "Vélo de route carbone",
                    "description": "Vélo de route en fibre de carbone, 21 vitesses, freins à disque.",
                    "price": 1599.99,
                    "stock": 5,
                },
                {
                    "category": "sports-loisirs",
                    "name": "Tapis de yoga premium",
                    "description": "Tapis de yoga antidérapant, épaisseur 6mm, matériau écologique.",
                    "price": 89.99,
                    "stock": 40,
                },
                {
                    "category": "livres",
                    "name": "Python pour les Nuls",
                    "description": "Guide complet pour apprendre Python, édition 2024.",
                    "price": 29.99,
                    "stock": 35,
                },
                {
                    "category": "livres",
                    "name": "Django par la pratique",
                    "description": "Livre sur le framework Django avec exemples concrets.",
                    "price": 39.99,
                    "stock": 18,
                },
                {
                    "category": "electronique",
                    "name": "Tablette iPad Air",
                    "description": "Tablette Apple iPad Air avec écran 10.9 pouces, 64GB.",
                    "price": 599.99,
                    "stock": 0,
                },
            ]

            for prod_data in products_data:
                category = categories[prod_data["category"]]
                product, created = Product.objects.get_or_create(
                    category=category,
                    slug=prod_data["name"]
                    .lower()
                    .replace(" ", "-")
                    .replace("é", "e")
                    .replace("è", "e")
                    .replace("à", "a"),
                    defaults={
                        "name": prod_data["name"],
                        "description": prod_data["description"],
                        "price": prod_data["price"],
                        "stock": prod_data["stock"],
                        "is_active": True,
                    },
                )
                if created:
                    self.stdout.write(f"  ✓ Produit créé: {product.name}")

        self.stdout.write(
            self.style.SUCCESS("Données de démonstration chargées avec succès!")
        )

