from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

### instances
class CustomUser(AbstractUser): ### as user in code
    tel = models.CharField(max_length=31,verbose_name="telephone number")
    adrs = models.CharField(max_length=63,verbose_name="adress")
    adrs2 = models.CharField(max_length=63,verbose_name="second adress",blank=True)
    post = models.CharField(max_length=15,verbose_name="post code")
    city = models.CharField(max_length=31)
    ### relation
    org = models.ForeignKey("Organization",on_delete=models.CASCADE,related_name="users",null=True,verbose_name="organization")

    class Meta:
        ordering = ['-last_login']
    def getter(_id:int): #getter by id
        instance = CustomUser.objects.filter(id=_id)
        if instance:
            return instance[0]
        else:
            return None
    def get_admin():
        L = CustomUser.objects.all()[:1]
        return L[0]
    
    def __str__(self):#to string
        return self.username
    
    ### saver
    # def clean(self):
    #     if not self.is_superuser:
    #         required_fields = ['tel','adrs','post','city']
    #         for field in required_fields:
    #             value = getattr(self,field)
    #             if not value:
    #                 raise ValidationError({field:f"field.replace('_',' ').capitalize is required for regular users."})
    # def save(self):
    #     self.clean()
    #     super().save(self)
            
    ### getters

class Organization(models.Model): ### as org in code
    #id_org = models.IntegerField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=63,unique=True,editable=True)
    tel = models.CharField(max_length=31,verbose_name="telephone number")
    adrs = models.CharField(max_length=63,verbose_name="adress")
    post = models.CharField(max_length=15,verbose_name="post code")

    class Meta:
        ordering = ['name']
    def getter(_id:int): #getter by id
        instance = Organization.objects.filter(id=_id)
        if instance:
            return instance[0]
        else:
            return None

    def __str__(self):#to string
        return self.name

class Contract(models.Model):  ### as con in code
    #id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=63,unique=True)
    nb_org = models.IntegerField(verbose_name="maximum of organization")
    nb_access = models.IntegerField(verbose_name="maximum of access")
    ### relation
    #org_pr = models.ForeignKey("Organization",on_delete=models.PROTECT,verbose_name="principal organization")
    org = models.ManyToManyField("Organization",related_name="cons",verbose_name="organizations")
    
    class Meta:
        ordering = ['name']
    def getter(_id:int): #getter by id
        instance = Contract.objects.filter(id=_id)
        if instance:
            return instance[0]
        else:
            return None
        
    def __str__(self):#to string
        return self.name

class Exercise(models.Model):  ### as exer in code
    #id = models.IntegerField(primary_key=True)
    name = models.CharField()
    date_i = models.DateField(verbose_name="start date")
    date_f = models.DateField(verbose_name="end date")
    period = models.DurationField(verbose_name="duration")
    EXER_TYPE = (
        ('1', 'Type1'),
        ('2', 'Type2'),
        ('3', 'Type3'),
        ('4', 'Type4'),
    )
    type = models.CharField(max_length=1,choices=EXER_TYPE,default='1')
    ### relation
    con = models.ForeignKey("Contract",on_delete=models.CASCADE,related_name="exers",verbose_name="contract")
    org = models.ForeignKey("Organization",on_delete=models.PROTECT,related_name="exers",verbose_name="organization in charge")
    
    class Meta:
        ordering = ['-date_i','-date_f']
    def getter(_id:int): #getter by id
        instance = Exercise.objects.filter(id=_id)
        if instance:
            return instance[0]
        else:
            return None
    def __str__(self): #to string
        return self.name
    
def file_path(instance,filename):
    # file will be uploaded to MEDIA_ROOT
    # con = instance['con']
    # exer = instance['exer']
    # name = instance['name']
    return "contract_{2}/exercise_{0}/{1}".format(
        instance.exer.id,
        instance.name,
        instance.con.id)

class File(models.Model):
    #id = models.IntegerField(primary_key=True)
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
    uploader = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="files_uploaded",null=True)#,default=CustomUser.get_admin()
    con = models.ForeignKey("Contract",on_delete=models.CASCADE,related_name="files",verbose_name="contract")
    exer = models.ForeignKey("Exercise",on_delete=models.CASCADE,related_name="files",verbose_name="exercise",null=True,blank=True)
    
    class Meta:
        ordering = ['name']
    def getter(_id:int): #getter by id
        instance = File.objects.filter(id=_id)
        if instance:
            return instance[0]
        else:
            return None
        
    def __str__(self):#to string
        return self.name
    
class Comment(models.Model):
    #id = models.IntegerField(primary_key=True)
    line = models.IntegerField()
    colone = models.IntegerField()
    text = models.TextField(max_length=4095)
    time = models.DateTimeField(auto_now=True)
    ### status
    is_treated = models.BooleanField(default=False)
    ### relation
    commenter = models.ForeignKey("CustomUser",on_delete=models.CASCADE,null=True,related_name="comments")#default=CustomUser.get_admin(),
    dealer = models.ForeignKey("CustomUser",on_delete=models.SET_NULL,null=True,blank=True,related_name="comments_to_deal")
    parent = models.ForeignKey("self",on_delete=models.CASCADE,null=True,blank=True,related_name='answers')
    file = models.ForeignKey("File",on_delete=models.CASCADE,related_name='comments')
    
    class Meta:
        ordering = ['file',]
    def getter(_id:int): #getter by id
        instance = Comment.objects.filter(id=_id)
        if instance:
            return instance[0]
        else:
            return None
        
    def __str__(self):#to string
        return self.text

### rights
class MailBell(models.Model):
    user = models.OneToOneField("CustomUser",on_delete=models.CASCADE,primary_key=True,related_name="mailbell")
    frequence = models.IntegerField(default=255)
    newfile = models.BooleanField(default=True)
    newchange = models.BooleanField(default=True)
    newcomment = models.BooleanField(default=True)
    newmessage = models.BooleanField(default=True)

    class Meta:
        ordering = ['user']
    def getter(_user:CustomUser): #getter by pk
        right = _user.mailbell.all()
        if right:
            return right[0]
        else:
            return None
        
    def __str__(self):#to string
        return CustomUser.__str__(self.user)

ROLE_TYPE = (
        ('A', 'Approver'),
        ('C', 'Contributer'),
        ('O', 'Observer'),
        ('S', 'Selfdefined'),
        ('U', 'Undefined'),
    )

class OrgConRight(models.Model):
    org = models.ForeignKey("Organization",on_delete=models.CASCADE,related_name="con_rights",verbose_name="organization")
    con = models.ForeignKey("Contract",on_delete=models.CASCADE,related_name="org_rights",verbose_name="contract")

    nb_access = models.IntegerField(verbose_name="maximum of access")
    # rights
    # exer_create = models.BooleanField(default=False)
    is_principal = models.BooleanField(default=False)
    staff = models.ManyToManyField("CustomUser",related_name="con")
    chief = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="con_staff",null=True)

    class Meta:
        ordering = ['org','con']
        unique_together = ('org','con')
    # def getter(_org:Organization,_con:Contract): #getter by pk
    #     right = OrgExerRight.objects.filter(org=_org,con=_con)
    #     if right:
    #         return right[0]
    #     else:
    #         return None
        
    def __str__(self):#to string
        return Contract.__str__(self.con)+Organization.__str__(self.org)
    
class UserConRight(models.Model):
    user = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="con_rights")
    con = models.ForeignKey("Contract",on_delete=models.CASCADE,related_name="user_rights",verbose_name="contract")
    # rights
    is_chief = models.BooleanField(default=False)
    # output = models.BooleanField(default=False)

    class Meta:
        ordering = ['user','con']
        unique_together = ('user','con')
    # def getter(_org:Organization,_con:Contract): # getter by pk
    #     right = OrgExerRight.objects.filter(org=_org,con=_con)
    #     if right:
    #         return right[0]
    #     else:
    #         return None
        
    def __str__(self):# to string
        return Contract.__str__(self.con)+CustomUser.__str__(self.user)

class OrgExerRight(models.Model):
    org = models.ForeignKey("Organization",on_delete=models.CASCADE,related_name="exer_rights",verbose_name="organization")
    exer = models.ForeignKey("Exercise",on_delete=models.CASCADE,related_name="org_rights",verbose_name="exercise")
    
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
        ordering = ['org','exer']
        unique_together = ('org','exer')
    # def getter(_org:Organization,_exer:Exercise): #getter by pk
    #     right = OrgExerRight.objects.filter(org=_org,exer=_exer)
    #     if right:
    #         return right[0]
    #     else:
    #         return None
        
    def __str__(self):#to string
        return Exercise.__str__(self.exer)+Organization.__str__(self.org)

class UserExerRight(models.Model):
    user = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="exer_rights")
    exer = models.ForeignKey("Exercise",on_delete=models.CASCADE,related_name="user_rights",verbose_name="exercise")
    
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
    # def getter(_user:Organization,_exer:Exercise): #getter by pk
    #     right = OrgExerRight.objects.filter(user=_user,exer=_exer)
    #     if right:
    #         return right[0]
    #     else:
    #         return None
        
    def __str__(self):#to string
        return Exercise.__str__(self.exer)+CustomUser.__str__(self.user)
    
class FileAccess(models.Model):
    file = models.OneToOneField("File",on_delete=models.CASCADE,primary_key=True,related_name="access")
    user = models.ManyToManyField("CustomUser",related_name="file_access")
    org = models.ManyToManyField("Organization",related_name="file_access",verbose_name="organization")

class Share(models.Model):
    from_user = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="share_to")
    to_user = models.ForeignKey("CustomUser",on_delete=models.CASCADE,related_name="shared_by")
    file = models.ForeignKey("File",on_delete=models.CASCADE,related_name="share")

    date = models.DateTimeField(auto_now=True)
    message = models.TextField(null=True,blank=True)
    between_org = models.BooleanField(default=False)
    class Meta:
        ordering = ['from_user','to_user','file']
        unique_together = ('from_user','to_user','file')
    
