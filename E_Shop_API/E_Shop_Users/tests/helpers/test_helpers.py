from datetime import date

from E_Shop_API.E_Shop_Users.models import Clients


def create_admin_user():
    return Clients.objects.create_user(
        first_name='Admin',
        last_name='Admin',
        email='admin@gmail.com',
        username='admin',
        password='AdminPass123',
        birth_date=date(1990, 1, 1),
        is_staff=True,
        is_superuser=True,
    )


def create_basic_user():
    return Clients.objects.create_user(
        username='User',
        first_name='User',
        last_name='User',
        email='user@gmail.com',
        password='UserPass123',
        birth_date=date(1990, 1, 1),
        is_staff=False,
        is_superuser=False,
    )
