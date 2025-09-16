"""
Serializers pour l'API REST de l'application catalog.
"""

from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Category, Product, Order, OrderItem

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer pour les catégories."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des produits (lecture seule)."""
    
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 
            'stock', 'is_active', 'category', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail des produits."""
    
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 
            'stock', 'is_active', 'category', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création/modification des produits."""
    
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'price', 
            'stock', 'is_active'
        ]
    
    def validate_price(self, value):
        """Valide que le prix est positif."""
        if value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif.")
        return value
    
    def validate_stock(self, value):
        """Valide que le stock est positif."""
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif.")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs (lecture seule)."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'address', 'is_gdpr_consent', 'gdpr_consent_date',
            'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'username', 'date_joined', 'last_login'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer pour les éléments de commande."""
    
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 
            'unit_price', 'total_price'
        ]
        read_only_fields = ['id', 'unit_price', 'total_price']
    
    def validate_quantity(self, value):
        """Valide que la quantité est positive."""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être positive.")
        return value


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des commandes."""
    
    user = UserSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total_amount', 
            'shipping_address', 'created_at', 'updated_at', 'items_count'
        ]
        read_only_fields = ['id', 'user', 'total_amount', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        """Retourne le nombre d'éléments dans la commande."""
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail des commandes."""
    
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total_amount', 
            'shipping_address', 'notes', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'total_amount', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de commandes."""
    
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'shipping_address', 'notes', 'items'
        ]
    
    def validate_items(self, value):
        """Valide que la commande contient au moins un élément."""
        if not value:
            raise serializers.ValidationError("La commande doit contenir au moins un produit.")
        return value
    
    def create(self, validated_data):
        """Crée une nouvelle commande avec ses éléments."""
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        total_amount = Decimal('0.00')
        order_items = []
        
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            if not product.is_active:
                raise serializers.ValidationError(
                    f"Le produit {product.name} n'est plus disponible."
                )
            if product.stock < item_data['quantity']:
                raise serializers.ValidationError(
                    f"Stock insuffisant pour {product.name}. "
                    f"Disponible: {product.stock}, Demandé: {item_data['quantity']}"
                )
            
            unit_price = product.price
            total_amount += unit_price * item_data['quantity']
            
            order_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'unit_price': unit_price
            })
        
        order = Order.objects.create(
            total_amount=total_amount,
            **validated_data
        )
        
        for item_data in order_items:
            OrderItem.objects.create(order=order, **item_data)
            
            product = item_data['product']
            product.stock -= item_data['quantity']
            product.save()
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification des commandes."""
    
    class Meta:
        model = Order
        fields = ['status', 'notes']
    
    def validate_status(self, value):
        """Valide les transitions de statut."""
        instance = self.instance
        if instance:
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['shipped', 'cancelled'],
                'shipped': ['delivered'],
                'delivered': [],
                'cancelled': []
            }
            
            if value not in valid_transitions.get(instance.status, []):
                raise serializers.ValidationError(
                    f"Transition de statut invalide de {instance.status} vers {value}"
                )
        return value


class UserGDPRExportSerializer(serializers.Serializer):
    """Serializer pour l'export RGPD des données utilisateur."""
    
    user_data = UserSerializer(read_only=True)
    orders = OrderDetailSerializer(many=True, read_only=True)
    export_date = serializers.DateTimeField(read_only=True)
    
    def to_representation(self, instance):
        """Formate les données pour l'export RGPD."""
        return {
            'user_data': UserSerializer(instance).data,
            'orders': OrderDetailSerializer(instance.orders.all(), many=True).data,
            'export_date': timezone.now().isoformat(),
            'export_purpose': 'RGPD - Droit à la portabilité des données',
            'data_retention_info': {
                'orders_retention': 'Conservées 10 ans pour obligations comptables',
                'personal_data_retention': 'Conservées jusqu\'à suppression du compte'
            }
        }
