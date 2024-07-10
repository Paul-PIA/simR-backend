# Generated by Django 5.0.6 on 2024-07-04 12:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0009_alter_userconright_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userconright',
            name='chief',
        ),
        migrations.AddField(
            model_name='orgconright',
            name='chief',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='con_staff', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='orgconright',
            name='staff',
            field=models.ManyToManyField(related_name='con', to=settings.AUTH_USER_MODEL),
        ),
    ]
