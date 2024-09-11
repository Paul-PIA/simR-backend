from django.utils.timezone import timedelta,now
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from .tasks import send_celery

# db_index=True accelerates the search
# unique_together means a unique multiset of a model

### instances
class CustomUser(AbstractUser): ### as user in code
    # The model of users, with details of the clients or administers i.e. the staff of PIA
    tel = models.CharField(max_length=31,verbose_name="telephone number")
    adrs = models.CharField(max_length=63,verbose_name="adress")
    adrs2 = models.CharField(max_length=63,verbose_name="second adress",blank=True)
    post = models.CharField(max_length=15,verbose_name="post code")
    city = models.CharField(max_length=31)
    ### relation
    org = models.ForeignKey("Organization",on_delete=models.CASCADE,related_name="users",verbose_name="organization",null=True,db_index=True)
    
    class Meta:
        ordering = ['-last_login']
    def __str__(self):#to string
        return self.username

class Organization(models.Model): ### as org in code
    # The model of organizations
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=63,unique=True,editable=True)
    tel = models.CharField(max_length=31,verbose_name="telephone number")
    adrs = models.CharField(max_length=63,verbose_name="adress")
    post = models.CharField(max_length=15,verbose_name="post code")

    class Meta:
        ordering = ['name']

    def __str__(self):#to string
        return self.name

class Contract(models.Model):  ### as con in code
    # composed by a list of organizations
    # which is the bord of the work and is independent between each other
    name = models.CharField(max_length=63,unique=True)
    nb_org = models.IntegerField(verbose_name="maximum of organization")
    nb_access = models.IntegerField(verbose_name="maximum of access")
    ### relation
    org = models.ManyToManyField("Organization",related_name="cons",verbose_name="organizations",db_index=True)
    
    class Meta:
        ordering = ['name']
    def __str__(self):#to string
        return self.name

EXER_TYPE = (
        ('1', 'Type1'), # a default type left, delete it or remain it on application
        ('G', 'Goal'),
        ('R', 'Review ex-post'),
        ('P', 'Plan'),
        ('A', 'Audit'),
    )
class Exercise(models.Model):  ### as exer in code
    # the minimal system of work in details 
    # in an organization on a template file, including the files
    name = models.CharField()
    date_i = models.DateField(verbose_name="start date")
    date_f = models.DateField(verbose_name="end date")
    period = models.DurationField(verbose_name="duration")
    
    type = models.CharField(max_length=1,choices=EXER_TYPE,default='1')
    ### relation
    con = models.ForeignKey("Contract",on_delete=models.CASCADE,related_name="exers",verbose_name="contract",db_index=True)
    org = models.ForeignKey("Organization",on_delete=models.PROTECT,related_name="exers",verbose_name="organization in charge",db_index=True)
    chief = models.ForeignKey("CustomUser",on_delete=models.PROTECT,related_name="exers",db_index=True)
    
    class Meta:
        ordering = ['-date_i','-date_f']
    def __str__(self): #to string
        return self.name
    
def file_path(instance,filename): # set the storage path of files uploaded
    return "contract_{0}/exercise_{1}/{2}".format(
        instance.con.id,
        instance.exer.id,
        instance.name
    )
class File(models.Model):
    # excel files, the core to work on in front-end, 
    # concluded in an exercise, which can be shared and commented
    name = models.CharField(max_length=63)
    content = models.FileField(upload_to=file_path)
    last_update = models.DateTimeField(auto_now=True,verbose_name="last update")
    ### status
    is_template = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_commented = models.BooleanField(default=False)
    is_boycotted = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    ### relation
    uploader = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="files_uploaded",db_index=True)
    con = models.ForeignKey("Contract",on_delete=models.CASCADE,related_name="files",verbose_name="contract",db_index=True)
    exer = models.ForeignKey("Exercise",on_delete=models.CASCADE,related_name="files",verbose_name="exercise",blank=True,db_index=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):#to string
        return self.name
    
class Comment(models.Model):
    # comments to the files, which can be answered, treated and distributed to somebody
    line = models.IntegerField()
    colone = models.IntegerField()
    text = models.TextField(max_length=4095)
    time = models.DateTimeField(auto_now_add=True)
    ### status
    is_treated = models.BooleanField(default=False)
    ### relation
    commenter = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="comments",db_index=True)
    dealer = models.ForeignKey("CustomUser",on_delete=models.SET_NULL,null=True,blank=True,related_name="comments_to_deal")
    parent = models.ForeignKey("self",on_delete=models.CASCADE,null=True,blank=True,related_name='answers')
    file = models.ForeignKey("File",on_delete=models.CASCADE,related_name='comments',db_index=True)
    
    class Meta:
        ordering = ['file',]        
    def __str__(self):#to string
        return self.text

def set_token(): # give a random token for invitation email
    return uuid.uuid4().__str__()
class Invitation(models.Model):
    # The model to send invitation emails to chief of a team and verify it
    token = models.CharField(default=set_token,unique=True)
    email = models.EmailField(max_length=63)
    activated_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(default=now()+timedelta(days=1))
    is_used = models.BooleanField(default=False)
    ### relation
    inviter = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="invitations")
    class Meta:
        ordering = ['id','activated_at','expired_at']        
    def __str__(self): # to string
        return self.token
    def is_expired(self):
        return now() > self.expired_at
    def send(self,right,message): # send invitation for right=right
        name = right.con.name
        if message == "" or message == None:
            message = f"Hello,\n{self.inviter.username} in {self.inviter.org} has sent you an invitation to participate in the contract {name}.\n"
            message += f"Please click this link http://127.0.0.1:8000/setchief/{right.id}/?token={self.token} to sign in as a chief."
        send_celery.delay(
            f"New invitation to the contract {name}",
            message,
            None,
            [self.email],
            False,
        )

EVENT_TYPE = ( # type of event written in the notification
    ('C', 'CREATE'),
    ('U', 'UPDATE'),
    ('D', 'DELETE'),
    ('S', 'SHARE'),
)
OBJ_TYPE = ( # type of object edited in the notification
    ('E', 'Exercise'),
    ('U', 'User'),
    ('F', 'File'),
    ('M', 'Comment'),
    ('C', 'Contract'),
    ('T', 'Team'),
    ('R', 'Right'),
)

class Notification(models.Model):
    # The model to record the recent operations
    actor = models.ForeignKey('CustomUser',on_delete=models.SET_NULL,null=True,related_name="action",db_index=True)
    receiver = models.ManyToManyField('CustomUser',related_name="notification",db_index=True)

    object = models.CharField(choices=OBJ_TYPE)
    event = models.CharField(choices=EVENT_TYPE)
    
    message = models.CharField(max_length=1023)
    trigger_time = models.DateTimeField() # time of action
    send_time = models.DateTimeField(auto_now_add=True) # time of sending notification
    # is_read = models.BooleanField(default=False) # I give up this, perhaps reuse it on application, but it needs to change a lot 

### rights
class MailBell(models.Model):
    user = models.OneToOneField("CustomUser",on_delete=models.CASCADE,primary_key=True,related_name="mailbell",db_index=True)
    frequence = models.IntegerField(default=255)
    newfile = models.BooleanField(default=True)
    newchange = models.BooleanField(default=True)
    newcomment = models.BooleanField(default=True)
    newmessage = models.BooleanField(default=True)

    class Meta:
        ordering = ['user']
    def __str__(self):#to string
        return CustomUser.__str__(self.user)

ROLE_TYPE = ( # role types in the exercises stored in the rights
    ('A', 'Approver'),
    ('C', 'Contributer'),
    ('O', 'Observer'),
    ('S', 'Selfdefined'),
    ('U', 'Undefined'),
)
class OrgConRight(models.Model):
    # The model of state of an organization in a contract
    # composed by a chief and a list of staff
    org = models.ForeignKey("Organization",on_delete=models.CASCADE,related_name="con_rights",verbose_name="organization",db_index=True)
    con = models.ForeignKey("Contract",on_delete=models.CASCADE,related_name="org_rights",verbose_name="contract",db_index=True)

    nb_access = models.IntegerField(verbose_name="maximum of access")
    # rights
    is_principal = models.BooleanField(default=False)
    staff = models.ManyToManyField("CustomUser",related_name="con_staff")
    chief = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="con_chief",null=True,db_index=True)

    class Meta:
        ordering = ['org','con']
        unique_together = ('org','con')
        
    def __str__(self):#to string
        return Contract.__str__(self.con)+Organization.__str__(self.org)

class OrgExerRight(models.Model):
    # Rights to participate in an exercise for an organization 
    # i.e. the rights of its chief in this contract
    # which can be decided by roles of approver, contributer, observer and self-defined
    org = models.ForeignKey("Organization",on_delete=models.CASCADE,related_name="exer_rights",verbose_name="organization",db_index=True)
    exer = models.ForeignKey("Exercise",on_delete=models.CASCADE,related_name="org_rights",verbose_name="exercise",db_index=True)
    
    role = models.CharField(max_length=1,choices=ROLE_TYPE,default='U')
    input = models.BooleanField(default=False)
    output = models.BooleanField(default=False) #two rights useless, i cant understand them, perhaps you will implement them on application
    graph = models.BooleanField(default=False) # the right to see the graph
    rewrite = models.BooleanField(default=False) # the right to edit
    #modifier les templates
    #exécuter les sénarios
    #modifier ses propres documents une fois partagé
    # the three fields perhaps are not pratical, but perhaps you will add them on application
    comment = models.BooleanField(default=False) # the right to comment
    download = models.BooleanField(default=False) # the right to download
    share = models.BooleanField(default=False) # the right to share

    class Meta:
        ordering = ['org','exer']
        unique_together = ('org','exer')
        
    def __str__(self):#to string
        return Exercise.__str__(self.exer)+Organization.__str__(self.org)

class UserExerRight(models.Model):
    # rights to participate in an exercise for a user, 
    # which can be decided by roles of approver, contributer, observer and self-defined
    user = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="exer_rights",db_index=True)
    exer = models.ForeignKey("Exercise",on_delete=models.CASCADE,related_name="user_rights",verbose_name="exercise",db_index=True)
    
    role = models.CharField(max_length=1,choices=ROLE_TYPE,default='U')
    input = models.BooleanField(default=False)
    output = models.BooleanField(default=False)
    graph = models.BooleanField(default=False)
    rewrite = models.BooleanField(default=False)
    #modifier les templates
    #exécuter les sénarios
    #modifier ses propres documents une fois partagé
    comment = models.BooleanField(default=False)
    download = models.BooleanField(default=False)
    share = models.BooleanField(default=False)

    class Meta:
        ordering = ['user','exer']
        unique_together = ('user','exer')
        
    def __str__(self):#to string
        return Exercise.__str__(self.exer)+CustomUser.__str__(self.user)
    
class FileAccess(models.Model): # record the orgs and users who can get access to the file
    file = models.OneToOneField("File",on_delete=models.CASCADE,primary_key=True,related_name="access",db_index=True)
    user = models.ManyToManyField("CustomUser",related_name="file_access")
    org = models.ManyToManyField("Organization",related_name="file_access",verbose_name="organization")

class Share(models.Model): # record the action of sharing
    from_user = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="share_to",db_index=True)
    to_user = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="shared_by",db_index=True)
    file = models.ForeignKey("File",on_delete=models.CASCADE,related_name="share",db_index=True)

    date = models.DateTimeField(auto_now_add=True)
    message = models.TextField(null=True,blank=True)
    between_org = models.BooleanField(default=False)
    class Meta:
        ordering = ['from_user','to_user','file']
        unique_together = ('from_user','to_user','file')
    
