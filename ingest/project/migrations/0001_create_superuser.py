import os
from uuid import uuid4
from django.db import migrations
from django.contrib.auth.models import User


def create_superuser(apps, schema_editor):
    username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
    if User.objects.filter(username=username).exists():
        print('Superuser already exists')
        return
    email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'test@example.com')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
    if not password:
        password = str(uuid4())
        print(f'''Generating random superuser password: {password}''')
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created successfully')


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(create_superuser),
    ]
