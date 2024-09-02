import os
from celery import Celery

# celery settings, don't touch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simR.settings')
app = Celery('simR')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()