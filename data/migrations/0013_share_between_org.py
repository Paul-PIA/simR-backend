# Generated by Django 5.0.6 on 2024-07-04 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0012_orgexerright_share_userexerright_share'),
    ]

    operations = [
        migrations.AddField(
            model_name='share',
            name='between_org',
            field=models.BooleanField(default=False),
        ),
    ]
