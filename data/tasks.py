import time
from django.core.mail import send_mail
from celery import shared_task

@shared_task
def add(x,y):
    print("sending...")
    time.sleep(10)
    print("successfully.")
    return x+y

@shared_task
def send_celery(_subject,_message,_from_email,_recipient_list,_fail_silently):
    send_mail(
        subject=_subject,
        message=_message,
        from_email=_from_email,
        recipient_list=_recipient_list,
        fail_silently=_fail_silently,
    )

@shared_task
def send_notification(receiver,actor,message,event,object,trigger_time):
    from .models import Notification,CustomUser
    notification = Notification.objects.create(
        actor = CustomUser.objects.get(id=actor),
        message = message,
        event = event,object = object,
        trigger_time=trigger_time
    )
    for user in receiver:
        notification.receiver.add(user)