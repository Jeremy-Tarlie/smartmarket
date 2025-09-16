import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="Nom"),
                ),
                (
                    "slug",
                    models.SlugField(max_length=100, unique=True, verbose_name="Slug"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de création"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Date de modification"
                    ),
                ),
            ],
            options={
                "verbose_name": "Catégorie",
                "verbose_name_plural": "Catégories",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="Email"
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True, max_length=20, verbose_name="Téléphone"
                    ),
                ),
                ("address", models.TextField(blank=True, verbose_name="Adresse")),
                (
                    "is_gdpr_consent",
                    models.BooleanField(
                        default=False, verbose_name="Consentement RGPD"
                    ),
                ),
                (
                    "gdpr_consent_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Date de consentement RGPD"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Utilisateur",
                "verbose_name_plural": "Utilisateurs",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("confirmed", "Confirmée"),
                            ("shipped", "Expédiée"),
                            ("delivered", "Livrée"),
                            ("cancelled", "Annulée"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Statut",
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Montant total",
                    ),
                ),
                (
                    "shipping_address",
                    models.TextField(verbose_name="Adresse de livraison"),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de création"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Date de modification"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Commande",
                "verbose_name_plural": "Commandes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="Nom")),
                ("slug", models.SlugField(max_length=200, verbose_name="Slug")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Description"),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Prix",
                    ),
                ),
                ("stock", models.PositiveIntegerField(default=0, verbose_name="Stock")),
                ("is_active", models.BooleanField(default=True, verbose_name="Actif")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date de création"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Date de modification"
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                        verbose_name="Catégorie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Produit",
                "verbose_name_plural": "Produits",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveIntegerField(verbose_name="Quantité")),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Prix unitaire",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="catalog.order",
                        verbose_name="Commande",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="catalog.product",
                        verbose_name="Produit",
                    ),
                ),
            ],
            options={
                "verbose_name": "Élément de commande",
                "verbose_name_plural": "Éléments de commande",
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["user", "status"], name="order_user_status_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["created_at"], name="order_created_at_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["slug"], name="product_slug_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["category", "is_active"], name="product_category_active_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("category", "slug"), name="unique_product_per_category"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("price__gte", 0)), name="price_non_negative"
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.UniqueConstraint(
                fields=("order", "product"), name="unique_order_product"
            ),
        ),
    ]
