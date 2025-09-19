"""
Routing WebSocket pour SmartMarket.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/admin/orders/$', consumers.AdminOrderConsumer.as_asgi()),
    re_path(r'ws/admin/notifications/$', consumers.AdminNotificationConsumer.as_asgi()),
    re_path(r'ws/user/(?P<user_id>\w+)/notifications/$', consumers.UserNotificationConsumer.as_asgi()),
]

