from django.db import migrations

def create_initial_employee(apps, schema_editor):
    Users = apps.get_model('users', 'Users')
    Employees = apps.get_model('employees', 'Employees')
    Audits = apps.get_model('employees', 'Audits')
    user = Users.objects.filter(email="test@example.com").first()
    if user:
        employee, _ = Employees.objects.get_or_create(
            user=user,
            defaults={
                'employee_file': "EMP001",
                'state': "active"
            }
        )
        Audits.objects.get_or_create(
            employee=employee,
            action="Create",
            observation="Creación de empleado de ejemplo",
            content_type_id=1,
            object_id=1
        )

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0002_initial'),
        ('users', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_initial_employee),
    ] 