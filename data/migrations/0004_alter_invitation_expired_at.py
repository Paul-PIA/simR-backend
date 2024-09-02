import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0003_notification'),
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='expired_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 26, 9, 57, 29, 44209, tzinfo=datetime.timezone.utc)),
        ),
    ]
