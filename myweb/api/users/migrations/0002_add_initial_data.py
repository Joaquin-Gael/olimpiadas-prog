from django.db import migrations
from datetime import date

def create_initial_user(apps, schema_editor):
    Users = apps.get_model('users', 'Users')
    # Hash de 'testpass123' generado por Django 4.x pbkdf2_sha256
    password_hash = 'pbkdf2_sha256$600000$wQn6QwQwQwQw$QwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQwQw=='
    user = Users.objects.filter(email="test@example.com").first()
    if not user:
        user = Users.objects.filter(telephone="123456789").first()
    if not user:
        user = Users.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            telephone="123456789",
            password=password_hash
        )

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_initial_user),
    ] 