"""
Commande pour créer les groupes et utilisateurs de démonstration.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Crée les groupes et utilisateurs de démonstration"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing data before creating',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write("Resetting existing data...")
            self.reset_data()

        self.stdout.write("Creating groups and permissions...")
        self.create_groups()

        self.stdout.write("Creating demo users...")
        self.create_users()

        self.stdout.write(
            self.style.SUCCESS("Successfully created groups and users")
        )

    def reset_data(self):
        """Supprime les données existantes."""
        User.objects.filter(is_superuser=False).delete()
        Group.objects.all().delete()

    def create_groups(self):
        """Crée les groupes et leurs permissions."""
        admin_group, created = Group.objects.get_or_create(name='admin')
        if created:
            admin_permissions = Permission.objects.all()
            admin_group.permissions.set(admin_permissions)
            self.stdout.write("  - Groupe 'admin' créé")

        manager_group, created = Group.objects.get_or_create(name='manager')
        if created:
            manager_permissions = Permission.objects.filter(
                content_type__app_label='catalog',
                codename__in=[
                    'add_category', 'change_category', 'delete_category', 'view_category',
                    'add_product', 'change_product', 'delete_product', 'view_product',
                    'add_order', 'change_order', 'view_order',
                    'add_orderitem', 'change_orderitem', 'view_orderitem',
                ]
            )
            manager_group.permissions.set(manager_permissions)
            self.stdout.write("  - Groupe 'manager' créé")

        client_group, created = Group.objects.get_or_create(name='client')
        if created:
            client_permissions = Permission.objects.filter(
                content_type__app_label='catalog',
                codename__in=[
                    'view_category', 'view_product',
                    'add_order', 'view_order',
                    'add_orderitem', 'view_orderitem',
                ]
            )
            client_group.permissions.set(client_permissions)
            self.stdout.write("  - Groupe 'client' créé")

    def create_users(self):
        """Crée les utilisateurs de démonstration."""
        with transaction.atomic():
            admin_user, created = User.objects.get_or_create(
                email='admin@smartmarket.com',
                defaults={
                    'username': 'admin',
                    'first_name': 'Admin',
                    'last_name': 'SmartMarket',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                    'is_gdpr_consent': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write("  - Utilisateur admin créé (admin@smartmarket.com / admin123)")

            manager_user, created = User.objects.get_or_create(
                email='manager@smartmarket.com',
                defaults={
                    'username': 'manager',
                    'first_name': 'Manager',
                    'last_name': 'SmartMarket',
                    'is_staff': False,
                    'is_active': True,
                    'is_gdpr_consent': True,
                }
            )
            if created:
                manager_user.set_password('manager123')
                manager_user.save()
                manager_user.groups.add(Group.objects.get(name='manager'))
                self.stdout.write("  - Utilisateur manager créé (manager@smartmarket.com / manager123)")

            client1_user, created = User.objects.get_or_create(
                email='client1@example.com',
                defaults={
                    'username': 'client1',
                    'first_name': 'Jean',
                    'last_name': 'Dupont',
                    'phone': '0123456789',
                    'address': '123 Rue de la Paix, 75001 Paris',
                    'is_staff': False,
                    'is_active': True,
                    'is_gdpr_consent': True,
                }
            )
            if created:
                client1_user.set_password('client123')
                client1_user.save()
                client1_user.groups.add(Group.objects.get(name='client'))
                self.stdout.write("  - Utilisateur client1 créé (client1@example.com / client123)")

            client2_user, created = User.objects.get_or_create(
                email='client2@example.com',
                defaults={
                    'username': 'client2',
                    'first_name': 'Marie',
                    'last_name': 'Martin',
                    'phone': '0987654321',
                    'address': '456 Avenue des Champs, 69000 Lyon',
                    'is_staff': False,
                    'is_active': True,
                    'is_gdpr_consent': True,
                }
            )
            if created:
                client2_user.set_password('client123')
                client2_user.save()
                client2_user.groups.add(Group.objects.get(name='client'))
                self.stdout.write("  - Utilisateur client2 créé (client2@example.com / client123)")
