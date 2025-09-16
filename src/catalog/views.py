"""
Vues pour l'application catalog.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView

from .models import Category, Product


class ProductListView(ListView):
    """Vue pour afficher la liste des produits."""

    model = Product
    template_name = "catalog/products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        """Retourne les produits actifs avec optimisation."""
        queryset = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .order_by("-created_at")
        )
        
        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all().order_by("name")
        return context


class ProductDetailView(DetailView):
    """Vue pour afficher le détail d'un produit."""

    model = Product
    template_name = "catalog/products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """Retourne les produits actifs avec optimisation."""
        return Product.objects.filter(is_active=True).select_related("category")

    def get_context_data(self, **kwargs):
        """Ajoute des données supplémentaires au contexte."""
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        context["related_products"] = (
            Product.objects.filter(category=product.category, is_active=True)
            .exclude(id=product.id)
            .select_related("category")[:4]
        )

        return context


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée."""
    
    template_name = 'catalog/auth/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirige vers le tableau de bord approprié selon le type d'utilisateur."""
        user = self.request.user
        
        if user.is_superuser:
            return reverse_lazy('admin:index')
        elif user.groups.filter(name='manager').exists():
            return reverse_lazy('catalog:manager_dashboard')
        elif user.groups.filter(name='client').exists():
            return reverse_lazy('catalog:client_dashboard')
        else:
            return reverse_lazy('catalog:product_list')


def logout_view(request):
    """Vue de déconnexion."""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('catalog:login')


class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord pour les managers."""
    
    template_name = 'catalog/dashboards/manager_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifie que l'utilisateur est un manager."""
        if not (request.user.is_superuser or request.user.groups.filter(name='manager').exists()):
            messages.error(request, 'Accès refusé. Vous devez être manager ou admin.')
            return redirect('catalog:product_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Ajoute des données au contexte."""
        context = super().get_context_data(**kwargs)
        
        context['total_products'] = Product.objects.count()
        context['active_products'] = Product.objects.filter(is_active=True).count()
        context['low_stock_products'] = Product.objects.filter(stock__lt=10, is_active=True).count()
        context['categories'] = Category.objects.all()
        
        return context


class ClientDashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord pour les clients."""
    
    template_name = 'catalog/dashboards/client_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifie que l'utilisateur est un client."""
        if not (request.user.is_superuser or request.user.groups.filter(name='client').exists()):
            messages.error(request, 'Accès refusé. Vous devez être client ou admin.')
            return redirect('catalog:product_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Ajoute des données au contexte."""
        context = super().get_context_data(**kwargs)
        
        context['user_orders'] = self.request.user.orders.all()[:5]
        context['categories'] = Category.objects.all()
        
        return context


class RGPDView(TemplateView):
    """Vue pour afficher la page RGPD et politique de confidentialité."""
    
    template_name = 'catalog/legal/rgpd.html'
