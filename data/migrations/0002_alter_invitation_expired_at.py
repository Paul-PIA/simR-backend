# Generated by Django 5.0.6 on 2024-08-01 14:34

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='expired_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 2, 16, 34, 34, 22397)),
        ),
    ]
