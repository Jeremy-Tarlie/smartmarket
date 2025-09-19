"""
Vues d'administration pour SmartMarket.
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import Order, User, Product


@staff_member_required
def admin_dashboard(request):
    """
    Tableau de bord d'administration avec WebSocket.
    """
    return render(request, 'admin/dashboard.html')


@staff_member_required
def admin_stats_api(request):
    """
    API pour les statistiques d'administration.
    """
    try:
        # Statistiques générales
        total_orders = Order.objects.count()
        today_orders = Order.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Utilisateurs actifs (dernière connexion dans les 7 derniers jours)
        week_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(
            last_login__gte=week_ago
        ).count()
        
        # Produits actifs
        active_products = Product.objects.filter(is_active=True).count()
        
        # Commandes par statut
        orders_by_status = {}
        for status, _ in Order.STATUS_CHOICES:
            orders_by_status[status] = Order.objects.filter(status=status).count()
        
        # Commandes des 7 derniers jours
        week_orders = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = Order.objects.filter(created_at__date=date).count()
            week_orders.append({
                'date': date.isoformat(),
                'count': count
            })
        
        return JsonResponse({
            'total_orders': total_orders,
            'today_orders': today_orders,
            'active_users': active_users,
            'active_products': active_products,
            'orders_by_status': orders_by_status,
            'week_orders': week_orders,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@staff_member_required
def admin_orders_api(request):
    """
    API pour les commandes d'administration.
    """
    try:
        # Paramètres de pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Filtres
        status = request.GET.get('status')
        user_id = request.GET.get('user_id')
        
        # Requête de base
        orders_query = Order.objects.select_related('user', 'product').order_by('-created_at')
        
        if status:
            orders_query = orders_query.filter(status=status)
        
        if user_id:
            orders_query = orders_query.filter(user_id=user_id)
        
        # Pagination
        total = orders_query.count()
        orders = orders_query[offset:offset + per_page]
        
        # Formatage des données
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'user': {
                    'id': order.user.id,
                    'username': order.user.username,
                    'email': order.user.email,
                },
                'product': {
                    'id': order.product.id,
                    'name': order.product.name,
                    'price': str(order.product.price),
                },
                'quantity': order.quantity,
                'total_price': str(order.total_price),
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'orders': orders_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

