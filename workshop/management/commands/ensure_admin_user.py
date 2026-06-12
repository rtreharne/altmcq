import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update a Django admin user from environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()

        if not username and not password and not email:
            self.stdout.write("Skipping admin user creation: no DJANGO_SUPERUSER_* variables set.")
            return

        if not username or not password:
            raise CommandError(
                "DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD must both be set to create or update the admin user."
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        updated_fields = []
        if user.email != email:
            user.email = email
            updated_fields.append("email")
        if not user.is_staff:
            user.is_staff = True
            updated_fields.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            updated_fields.append("is_superuser")
        if not user.check_password(password):
            user.set_password(password)
            updated_fields.append("password")

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}' from environment variables."))
            return

        if updated_fields:
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated admin user '{username}' from environment variables ({', '.join(updated_fields)})."
                )
            )
            return

        self.stdout.write(f"Admin user '{username}' already matches environment variables.")
