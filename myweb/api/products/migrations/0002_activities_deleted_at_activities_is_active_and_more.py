# Generated by Django 5.2.3 on 2025-06-29 04:00

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='activities',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='activities',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='flights',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flights',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='lodgments',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lodgments',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='packages',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='productsmetadata',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='productsmetadata',
            name='end_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='productsmetadata',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='productsmetadata',
            name='start_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='transportation',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transportation',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='activities',
            name='difficulty_level',
            field=models.CharField(choices=[('Very Easy', 'Very_Easy'), ('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Very Hard', 'Very_Hard'), ('Extreme', 'Extreme')], max_length=16),
        ),
        migrations.AlterField(
            model_name='flights',
            name='class_flight',
            field=models.CharField(choices=[('Basic Economy', 'Basic_Economy'), ('Economy', 'Economy'), ('Premium Economy', 'Premium_Economy'), ('Business Class', 'Business'), ('First Class', 'First')], max_length=16),
        ),
        migrations.AlterField(
            model_name='packages',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='productsmetadata',
            name='product_type',
            field=models.CharField(choices=[('ACTIVITY', 'Activity'), ('FLIGHT', 'Flight'), ('LODGMENT', 'Lodgment'), ('TRANSPORTATION', 'Transportation')], help_text='Tipo de product: actividad, vuelo, alojamiento, transporte'),
        ),
    ]
