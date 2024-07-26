from django.db.models.signals import pre_delete,pre_init,pre_save,post_delete,post_init,post_save
from django.dispatch import receiver

from .models import CustomUser,Organization,Contract,Exercise,File,Comment,Invitation
from .models import FileAccess,MailBell,Share,OrgConRight,OrgExerRight,UserExerRight
from .tasks import send_notification

@receiver(post_save,sender=UserExerRight)
def update_rights():
    return

@receiver(post_save,sender=File)
def upload_file(sender,instance,created,update_fields,**kwargs):
    return
@receiver(post_save,sender=File)
def update_file(sender,instance,created,update_fields,**kwargs):
    return
@receiver(post_save,sender=File)
def publish_file(sender,instance,created,update_fields,**kwargs):
    return
@receiver(post_delete,sender=File)
def delete_file(sender,instance,**kwargs):
    return
@receiver(post_save,sender=Share)
def share_file(sender,instance,created,update_fields,**kwargs):
    return
@receiver(post_save,sender=Comment)
def comment_file(sender,instance,created,update_fields,**kwargs):
    return
@receiver(post_save,sender=Comment) #OK
def deal_comment():
    return

@receiver(post_save,sender=Contract) #OK
def set_orgs():
    return

@receiver(post_save,sender=OrgConRight) #OK
def set_staff():
    return
@receiver(post_save,sender=OrgConRight) #OK
def reset_distribution():
    return
@receiver(post_save,sender=OrgConRight) #OK
def register_chief():
    return

@receiver(post_save,sender=CustomUser) #OK
def become_admin(sender,instance,created,update_fields,**kwargs):
    return
@receiver(post_save,sender=Exercise) #OK
def create_exer(sender,instance,created,update_fields,**kwargs):
    return
@receiver(post_save,sender=Exercise) #OK
def reset_exer(sender,instance,created,update_fields,**kwargs):
    return