from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Set passwords for users'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Definir contraseñas para cada usuario por su email o ID
        users_passwords = {
            'admin@example.com': 'adminpassword',
            'worker@example.com': 'workerpassword',
            'client@example.com': 'clientpassword',
            'owner@example.com': 'ownerpassword',
        }
        
        for email, password in users_passwords.items():
            try:
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully set password for {email}'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {email} does not exist'))
