"""
Consumers WebSocket pour SmartMarket.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

User = get_user_model()
logger = logging.getLogger(__name__)


class AdminOrderConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications de commandes en temps réel pour les admins."""
    
    async def connect(self):
        """Connexion WebSocket pour les admins."""
        self.room_group_name = 'admin_orders'
        
        # Vérifier l'authentification et les permissions
        if not await self.check_admin_permissions():
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Admin connected to orders channel: {self.scope['user']}")
        
        # Envoyer un message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to admin orders channel',
            'timestamp': self.get_timestamp()
        }))
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Admin disconnected from orders channel: {close_code}")
    
    async def receive(self, text_data):
        """Réception de messages du client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.get_timestamp()
                }))
            elif message_type == 'get_recent_orders':
                await self.send_recent_orders()
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def order_created(self, event):
        """Envoi d'une notification de nouvelle commande."""
        await self.send(text_data=json.dumps({
            'type': 'order_created',
            'order': event['order'],
            'timestamp': event['timestamp']
        }))
    
    async def order_updated(self, event):
        """Envoi d'une notification de commande mise à jour."""
        await self.send(text_data=json.dumps({
            'type': 'order_updated',
            'order': event['order'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def check_admin_permissions(self):
        """Vérifier que l'utilisateur est un admin."""
        user = self.scope.get('user')
        
        if not user or user.is_anonymous:
            return False
        
        # Vérifier si l'utilisateur est staff ou superuser
        return user.is_staff or user.is_superuser
    
    @database_sync_to_async
    def get_recent_orders(self):
        """Récupérer les commandes récentes."""
        from .models import Order
        
        orders = Order.objects.select_related('user', 'product').order_by('-created_at')[:10]
        
        return [
            {
                'id': order.id,
                'user': {
                    'id': order.user.id,
                    'username': order.user.username,
                },
                'product': {
                    'id': order.product.id,
                    'name': order.product.name,
                },
                'quantity': order.quantity,
                'total_price': str(order.total_price),
                'status': order.status,
                'created_at': order.created_at.isoformat(),
            }
            for order in orders
        ]
    
    async def send_recent_orders(self):
        """Envoyer les commandes récentes."""
        orders = await self.get_recent_orders()
        await self.send(text_data=json.dumps({
            'type': 'recent_orders',
            'orders': orders,
            'timestamp': self.get_timestamp()
        }))
    
    def get_timestamp(self):
        """Obtenir le timestamp actuel."""
        from django.utils import timezone
        return timezone.now().isoformat()


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications générales des admins."""
    
    async def connect(self):
        """Connexion WebSocket pour les notifications admin."""
        self.room_group_name = 'admin_notifications'
        
        # Vérifier l'authentification et les permissions
        if not await self.check_admin_permissions():
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Admin connected to notifications channel: {self.scope['user']}")
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Admin disconnected from notifications channel: {close_code}")
    
    async def receive(self, text_data):
        """Réception de messages du client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.get_timestamp()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def system_notification(self, event):
        """Envoi d'une notification système."""
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'notification': event['notification'],
            'timestamp': event['timestamp']
        }))
    
    async def ml_task_completed(self, event):
        """Envoi d'une notification de tâche ML terminée."""
        await self.send(text_data=json.dumps({
            'type': 'ml_task_completed',
            'task': event['task'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def check_admin_permissions(self):
        """Vérifier que l'utilisateur est un admin."""
        user = self.scope.get('user')
        
        if not user or user.is_anonymous:
            return False
        
        return user.is_staff or user.is_superuser
    
    def get_timestamp(self):
        """Obtenir le timestamp actuel."""
        from django.utils import timezone
        return timezone.now().isoformat()


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications utilisateur."""
    
    async def connect(self):
        """Connexion WebSocket pour les notifications utilisateur."""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'user_{self.user_id}_notifications'
        
        # Vérifier l'authentification
        if not await self.check_user_permissions():
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user_id} connected to notifications channel")
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user_id} disconnected from notifications channel: {close_code}")
    
    async def receive(self, text_data):
        """Réception de messages du client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.get_timestamp()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def user_notification(self, event):
        """Envoi d'une notification utilisateur."""
        await self.send(text_data=json.dumps({
            'type': 'user_notification',
            'notification': event['notification'],
            'timestamp': event['timestamp']
        }))
    
    async def order_status_update(self, event):
        """Envoi d'une notification de mise à jour de commande."""
        await self.send(text_data=json.dumps({
            'type': 'order_status_update',
            'order': event['order'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def check_user_permissions(self):
        """Vérifier que l'utilisateur peut accéder à ses notifications."""
        user = self.scope.get('user')
        
        if not user or user.is_anonymous:
            return False
        
        # Vérifier que l'utilisateur accède à ses propres notifications
        return str(user.id) == self.user_id
    
    def get_timestamp(self):
        """Obtenir le timestamp actuel."""
        from django.utils import timezone
        return timezone.now().isoformat()

