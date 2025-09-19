"""
URLs pour l'application catalog.
"""

from django.urls import path

from . import views
from . import admin_views
from . import health_views

app_name = "catalog"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path("p/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    path("manager/", views.ManagerDashboardView.as_view(), name="manager_dashboard"),
    path("client/", views.ClientDashboardView.as_view(), name="client_dashboard"),
    
    path("rgpd/", views.RGPDView.as_view(), name="rgpd"),
    
    # URLs d'administration
    path("admin/dashboard/", admin_views.admin_dashboard, name="admin_dashboard"),
    path("admin/api/stats/", admin_views.admin_stats_api, name="admin_stats_api"),
    path("admin/api/orders/", admin_views.admin_orders_api, name="admin_orders_api"),
    
    # URLs de health check
    path("health/live/", health_views.health_live, name="health_live"),
    path("health/ready/", health_views.health_ready, name="health_ready"),
    path("health/detailed/", health_views.health_detailed, name="health_detailed"),
]

