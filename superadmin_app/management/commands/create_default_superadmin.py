from django.core.management.base import BaseCommand
from superadmin_app.models import Profiles


class Command(BaseCommand):
    help = 'Creates a default superadmin if one does not exist'

    def handle(self, *args, **kwargs):
        email = 'admin@test.com'

        if Profiles.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING('Default superadmin already exists.')
            )
            return

        Profiles.objects.create_superuser(
            email=email,
            password='Admin@123',
            username='superadmin',
            fullname='Render Test Admin'
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Default superadmin created successfully.'
            )
        )