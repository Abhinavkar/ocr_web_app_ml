# Generated by Django 5.1.3 on 2024-12-16 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qa', '0002_class_subject'),
    ]

    operations = [
        migrations.AlterField(
            model_name='class',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
