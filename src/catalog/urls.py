"""
URLs pour l'application catalog.
"""

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path("p/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    path("manager/", views.ManagerDashboardView.as_view(), name="manager_dashboard"),
    path("client/", views.ClientDashboardView.as_view(), name="client_dashboard"),
    
    path("rgpd/", views.RGPDView.as_view(), name="rgpd"),
]

