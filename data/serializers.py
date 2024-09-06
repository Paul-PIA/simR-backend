# handle the operations on db
# __init__,validate,CRUD
import uuid

from rest_framework import serializers
from rest_framework.serializers import PrimaryKeyRelatedField as PKRF
from django.db import models
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist as ODNE
from django.core.mail import send_mail

from .models import CustomUser,Organization,Contract,Exercise,File,Comment,Invitation,Notification
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserExerRight
from .permissions import get_chief
from .tasks import send_celery,send_notification

class ShareSerializer(serializers.ModelSerializer):
    from_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Share
        fields = '__all__'
        read_only_fields = ['id','from_user',]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None: # modification forbidden
            self.fields['to_user'].read_only =True
            self.fields['date'].read_only =True
            self.fields['file'].read_only =True
            self.fields['between_org'].read_only =True
    def validate(self, attrs):
        if self.instance is not None: # skip while updating
            return super().validate(attrs)
        # while sharing
        attrs['from_user'] = self.context['request'].user
        if attrs.get('to_user',None) == attrs['from_user']: #refuse sharing to itself
            raise serializers.ValidationError("It's no use to share it to yourself.")
        to_user = attrs['to_user']
        org = to_user.org
        con = attrs['file'].con
        right = OrgConRight.objects.filter(con=con,org=org)
        if not right.exists():
                raise serializers.ValidationError("The receiver's organization isn't in the contract.")
        if attrs.get('between_org',None): # while sharing to a new org 
            if org == attrs['from_user'].org: #refuse sharing to its own org
                raise serializers.ValidationError("It's no use to share it to your organization.")
            chief = right.first().chief
            if not chief: #refuse sharing to orgs without chief
                raise serializers.ValidationError("The chief hasn't validated.")
            if chief != to_user:
                raise serializers.ValidationError("Share between organizations must be to the certain chief.")
        else: # while sharing to a colleague
            if not to_user in right.first().staff.all():
                raise serializers.ValidationError("The receiver isn't in your team.")
        return super().validate(attrs)
    def create(self, validated_data):
        file = validated_data['file']
        to_user = validated_data['to_user']
        access = FileAccess.objects.get(file=file)
        access.user.add(to_user) # add right to access the file
        if validated_data.get('between_org',None):
            access.org.add(to_user.org) # add right to access the file
        if to_user.mailbell.newfile: # send email
            send_celery(
                "New file shared to you",
                f"Hello, {to_user}\n {validated_data['from_user'].username} has shared the file {file.name} with you, with message as:\n {validated_data['message']}",
                None,
                [to_user.email],
                fail_silently=False,
            )
        return super().create(validated_data)
class MailBellSerializer(serializers.ModelSerializer):
    user = PKRF(queryset=CustomUser.objects.all())
    class Meta:
        model = MailBell
        fields = '__all__'
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None:
            self.fields['user'].read_only =True
class FileAccessSerializer(serializers.ModelSerializer):
    file = PKRF(queryset=File.objects.all())
    class Meta:
        model = FileAccess
        fields = '__all__'
        read_only_fields = ['file','user','org']

def chiefrightcopy(user:CustomUser,exer:Exercise,actor:CustomUser): # to copy the the exer_right from org to its chief
    right = OrgExerRight.objects.get(exer=exer,org__users=user)
    chiefright = UserExerRight.objects.get(exer=exer,user=user)
    chiefright.role = right.role
    chiefright.input = right.input
    chiefright.output = right.output
    chiefright.graph = right.graph
    chiefright.rewrite = right.rewrite
    chiefright.comment = right.comment
    chiefright.download = right.download
    chiefright.share = right.share
    chiefright.save()
    trigger_time = timezone.now()
    message = f"Your right in exercise {exer.name} is reset."
    send_notification.delay(
        receiver = [user.id],#list of ids
        actor = actor.id, # id
        message = message,event = 'U',object = 'R',
        trigger_time = trigger_time
    )

class OrgConRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgConRight
        fields = '__all__'
        read_only_fields = ['id','org','con','is_principal','nb_access','chief']
    def validate_staff(self,value):
        if len(value)>self.instance.nb_access:
            raise serializers.ValidationError("List of staff is too long.")
        if self.instance.chief not in value: # chief is staff
            raise serializers.ValidationError("Chief isn't in the staff.")
        org = self.instance.org
        ids = [user.id for user in value]
        users = CustomUser.objects.select_related('org').filter(id__in=ids) # simplify query
        for user in users: # staff is in the org
            if org != user.org:
                raise serializers.ValidationError("Staff must be in the Organization.")
        return value
    # def validate_nb_access(self,value):
    #     if value<len(self.instance.staff.all()):#number of access>number of staff
    #         raise serializers.ValidationError("Number of account can't be less than the number of staff.")
    #     con = self.instance.con
    #     org_0 = self.instance.org
    #     sum = 0
    #     orgs = con.org.all()
    #     rights = OrgConRight.objects.select_related("org").filter(con=con) # simplify query
    #     for org in orgs:
    #         if org != org_0:
    #             sum += rights.get(org=org).nb_access
    #     if value > con.nb_access-sum:#number of access<the number left
    #         raise serializers.ValidationError("Number of account is too big.")
    #     return value
    # def validate(self, attrs):
    #     chief = attrs.get('chief',None)
    #     if self.instance.chief is None and chief is None:#locked before validation of chief
    #         raise serializers.ValidationError("The chief has not validated.")
    #     return super().validate(attrs)
    def update(self, instance, validated_data):
        con = instance.con
        staff_old = instance.staff.all()
        staff_new = validated_data['staff']
        exers = Exercise.objects.filter(con=con)
        # delete old relationship
        rights = UserExerRight.objects.select_related('user').filter(exer__in=exers) # simplify query
        rights.exclude(user__in=staff_new).filter(user__in=staff_old).delete()
        for user in staff_new: # create new relationship
            if not (user in staff_old):
                for exer in exers:
                    UserExerRight.objects.create(user=user,exer=exer)
        right = super().update(instance, validated_data)
        return right
class OrgExerRightSerializer(serializers.ModelSerializer):
    #set by principal chief
    class Meta:
        model = OrgExerRight
        fields = '__all__'
        read_only_fields = ['id','org','exer']
    def update(self, instance, validated_data):
        right = super().update(instance, validated_data)
        try:
            chief = get_chief(right)
            actor = self.context['request'].user
            chiefrightcopy(chief,instance.exer,actor) # copy the right
        except CustomUser.DoesNotExist:
            pass
        return right
class UserExerRightSerializer(serializers.ModelSerializer):
    # set by each chief
    class Meta:
        model = UserExerRight
        fields = '__all__'
        read_only_fields = ['id','user','exer']
    def validate(self, attrs): # to update
        right = self.instance
        for key in attrs.keys():
            if attrs.get(key) and (not getattr(right,key)):
                raise serializers.ValidationError(f"The right {key} for your organization isn't accessible in this exercise.")
        return super().validate(attrs)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','username','first_name','last_name','email','tel','adrs','adrs2','org','post','city']
        read_only_fields = ['id']
    def validate_org(self,value):
        if self.instance and self.instance.org and value:
            raise serializers.ValidationError("Parameter org is read-only once set.")
        else:
            return value
    def validate(self, attrs):#update org
        org = attrs.get('org',None)
        org_0 = self.instance.org
        if org_0 and org is not None: # can't be modified once set
            raise serializers.ValidationError("The organization can't be modified.")
        if not org_0 and org is None: # necessary to set it if it's null 
            raise serializers.ValidationError("The organization is neccessary.")
        return super().validate(attrs)
    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        try: # automatically create the mailbell
            mb = instance.mailbell
        except ODNE:
            MailBell.objects.create(user=instance)
        return user
class OrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ['id']
class ConSerializer(serializers.ModelSerializer):
    org = PKRF(queryset=Organization.objects.all(),many=True)
    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = ['id',]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None:
            self.fields['nb_org'].read_only =True
            self.fields['nb_access'].read_only =True
    def validate(self, attrs):
        if self.instance is not None: #update
            nb_org = self.instance.nb_org
            orgs_new = attrs.get('org',None)
            if orgs_new is None: # org lists required
                raise serializers.ValidationError("List org is always required.")
            if len(orgs_new) > nb_org: # refuse too many orgs
                raise serializers.ValidationError("List org is too long.")
            org = OrgConRight.objects.select_related('org').get(con=self.instance,is_principal=True).org
            if org not in orgs_new:
                raise serializers.ValidationError("The principal organization must be in.")
            orgs_old = self.instance.org.all()
            exers = Exercise.objects.select_related('org').filter(con=self.instance) # simplify query
            if exers.exclude(org__in=orgs_new).filter(org__in=orgs_old).exists():
                raise serializers.ValidationError("The organization that takes charge of an exercise can't be deleted.")     
        else: #create
            if len(attrs['org']) != 1:
                raise serializers.ValidationError("Only the principal organization is supposed to be decided.")
        return super().validate(attrs)
    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     data['org']= data['org_detail']
    #     return data
    def create(self, validated_data):
        contract = super().create(validated_data)
        org = contract.org.first()
        right = OrgConRight.objects.create( # create the right
            org=org,con=contract,is_principal=True,nb_access=1,
        )
        return contract
    def update(self, instance, validated_data):
        orgs_old = list(instance.org.all())
        orgs_new = validated_data['org']
        contract = super().update(instance, validated_data)
        exers = Exercise.objects.filter(con=contract)
        # simplify the query
        userexer = UserExerRight.objects.select_related('user').filter(exer__in=exers)
        orgcon = OrgConRight.objects.select_related('org').prefetch_related('staff').filter(con=contract)
        orgexer = OrgExerRight.objects.select_related('org').filter(exer__in=exers)
        # delete old relationship
        orgcon = orgcon.exclude(org__in=orgs_new).filter(org__in=orgs_old)
        for right in orgcon:
            userexer.filter(user__in=right.staff.all()).delete()
        orgcon.delete()
        orgexer.exclude(org__in=orgs_new).filter(org__in=orgs_old).delete()
        # create new relationship
        for org in orgs_new:
            if not (org in orgs_old):
                OrgConRight.objects.create(con=contract,org=org,nb_access=1)
                for exer in exers:
                    OrgExerRight.objects.create(exer=exer,org=org)
        return contract
class ExerSerializer(serializers.ModelSerializer):
    chief = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Exercise
        fields = '__all__'
        read_only_fields = ['id']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None:
            self.fields['con'].read_only =True
            self.fields['org'].read_only =True
    def validate_org(self,value):
        user = self.context['request'].user
        if user.org != value:
            raise serializers.ValidationError("You're not in the organization.")
        return value
    def validate(self, attrs):
        return super().validate(attrs)
    def create(self, validated_data):
        user = self.context['request'].user
        org = user.org
        exercise = super().create(validated_data)
        contract = validated_data['con']
        orgs = contract.org.all()
        rights = OrgConRight.objects.select_related('org').prefetch_related('staff').filter(con=contract) # simplify the query
        for _org in orgs: # create rights for orgs
            if _org == org:
                OrgExerRight.objects.create(
                    org=_org,exer=exercise,role='A',
                    input=True,output=True,graph=True,
                    rewrite=True,comment=True,download=True,share=True,
                )
            else:
                OrgExerRight.objects.create(org=_org,exer=exercise)
            users = rights.get(org=_org).staff.all()
            for _user in users: # create rights for users
                if _user == user:
                    UserExerRight.objects.create(
                        user=_user,exer=exercise,role='A',
                        input=True,output=True,graph=True,rewrite=True,
                        comment=True,download=True,share=True,
                    )
                else:
                    UserExerRight.objects.create(user=_user,exer=exercise,)
        return exercise

class FileSerializer(serializers.ModelSerializer):
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['id','last_update','is_locked','is_commented','is_boycotted','is_final','is_public']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None: # restrict for file uploaded
            self.fields['uploader'].read_only = True
            self.fields['con'].read_only = True
            self.fields['exer'].read_only = True
            self.fields['is_template'].read_only = True
        # else: #auto set name while uploading
        #     request = self.context['request']
        #     data = request.data
        #     if data['name'] == "":
        #         data['name'] = request.FILES.get('content').name
        #     else:
        #         data['name'] = data['name'] + ".xlsx"
    def validate(self, attrs):
        request = self.context['request']
        if self.instance is not None: # while updating
            if request.method != 'GET':
                if self.instance.is_locked or self.instance.is_final: # protect locked file
                    raise serializers.ValidationError("Any modification to this file is prohibited.")
            if attrs.get('name',None) is not None: # auto set name
                attrs['name'] = attrs['name'] + ".xlsx"
        else: # while uploading
            if attrs.get('exer',None) is not None:
                if attrs['exer'].con != attrs['con']:
                    raise serializers.ValidationError("The exercise isn't in the contract.")
            for value in request.FILES.values():
                if not (value.name.endswith('.xlsx') or value.name.endswith('.xls')):
                    raise serializers.ValidationError("Only the types .xlsx and .xls are accepted.")
        return super().validate(attrs)
    def create(self, validated_data):
        user = self.context['request'].user
        file = super().create(validated_data)
        # create and distribute access
        access = FileAccess.objects.create(file=file)
        access.user.add(user)
        access.org.add(user.org)
        return file
class CommentSerializer(serializers.ModelSerializer):
    commenter = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['id','is_treated','dealer',]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None:
            self.fields['line'].read_only = True
            self.fields['colone'].read_only = True
            self.fields['commenter'].read_only = True
            self.fields['parent'].read_only = True
            self.fields['file'].read_only = True
            self.fields['time'].read_only = True
    def validate(self, attrs):
        parent = attrs.get('parent',None)
        if parent is not None: #identify to parent
            for key in ['line','colone','file']:
                value = attrs.get(key,None)
                if (value is not None) and (value!=getattr(parent,key)):
                    raise serializers.ValidationError("Position and file must be the same of parent comment.")
        return super().validate(attrs)
    def create(self, validated_data):
        comment = super().create(validated_data)
        parent = validated_data.get('parent',None)
        if parent is not None: #identify to parent
            for key in ['line','colone','file']:
                value = validated_data.get(key,None)
                if value is None:
                    validated_data[key] = getattr(parent,key)
        file = validated_data['file']
        file.is_commented = True # turn on the file
        file.save()
        chief = get_chief(file)
        if chief.mailbell.newcomment: # send email
            send_celery(
                "New comment to file",
                f"Hello, {chief.username}\n {self.context['request'].user.username} has commented to the file {file.name}, with content as:\n {validated_data['text']}",
                None,
                [chief.email],
                fail_silently=False,
            )
        return comment

# interior serializers, can't be used directly
class InvitationSerializer(serializers.ModelSerializer):
    message = serializers.CharField()
    subject = serializers.CharField()
    class Meta:
        model = Invitation
    #     fields = '__all__'
    # def validate_email(self,value):
    #     try:
    #         CustomUser.objects.get(email=value)
    #         return value
    #     except Contract.DoesNotExist:
    #         raise serializers.ValidationError("The email does not exist.")
    # def validate(self, attrs):
    #     message = attrs.get("message",None)
    #     subject = attrs.get("subject",None)
    #     if (message is not None) and (subject is not None):
    #         return super().validate(attrs)
    #     else:
    #         raise serializers.ValidationError("The subject and message are both required.")
    # def create(self, validated_data):
    #     invitation = super().create(validated_data)
    #     message = validated_data.get("message",None)
    #     subject = validated_data.get("subject",None)
    #     send_celery.delay(
    #         subject,
    #         message,
    #         None,
    #         [invitation.email],
    #         fail_silently=False,
    #     )
    #     invitation.inviter=CustomUser.objects.get(email=invitation.email)
    #     invitation.save()
    #     return invitation

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

# Certain getters, perhaps abandonned
class SpaceShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = ['file','from_user','to_user','date','between_org']
        read_only_fields = ['file','from_user','to_user','date']
class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['name',]
        read_only_fields = ['name',]
class PrintCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['commenter','time','text','parent']
        read_only_fields = ['commenter','time','text','parent']

# Certain evaluaters
class SetUserStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','is_active','is_staff','is_superuser']
        read_only_fields = ['id',]
class SetFileStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id','is_locked','is_final','is_public']
        read_only_fields = ['id',]
class DistributeAccountSerializer(serializers.ModelSerializer):
    distribution = serializers.JSONField()
    class Meta:
        model = Contract
        fields = ['id','nb_access','distribution']
        read_only_fields = ['id',]
    def validate(self, attrs):
        dis = attrs.get('distribution',None) # a distribution in json format
        if dis is not None: # set new distribution
            orgs = self.instance.org.all()
            rights = OrgConRight.objects.select_related('org').prefetch_related('staff').filter(con=self.instance) # simplify the query
            for org in orgs: # check every org
                new_number = dis.get(org.name,None) # get distribution
                if new_number is not None and isinstance(new_number,int): # if new distribution is normal
                    old_number = rights.get(org=org).staff.count()
                    if new_number < old_number:
                        raise serializers.ValidationError("The new distribution can't be less than the staff registered.")
                elif new_number is not None:
                    raise serializers.ValidationError("The new distribution contains non-number.")
            s = sum(dis.values()) # count the amount of accounts
        else: # no new distribution
            s = 0
        if attrs.get('nb_access',None): # set amount in total
            nb_access = attrs['nb_access']
            if not isinstance(nb_access,int):
                raise serializers.ValidationError("The new maximum isn't a number.")
        else:
            nb_access = self.instance.nb_access
        if s > nb_access:
            raise serializers.ValidationError("The sum of accounts is over the maximum.")
        return super().validate(attrs)
    def update(self, instance, validated_data):
        dis = validated_data.get('distribution',None)
        if dis is not None: # when redo the distribution
            orgs = self.instance.org.all()
            rights = OrgConRight.objects.select_related('org').filter(con=self.instance) # simplify the query
            for org in orgs:
                new_number = dis.get(org.name,None)
                if new_number is not None:
                    right = rights.get(org=org)
                    right.nb_access = new_number
                    right.save()
        return super().update(instance, validated_data)

class AssignCommentSerializer(serializers.ModelSerializer):
    # to assign a comment to a member to deal with
    class Meta:
        model = Comment
        fields = ['id','dealer']
        read_only_fields = ['id',]
    def validate(self, attrs):
        dealer = attrs['dealer']
        user = self.context['request'].user
        right = OrgConRight.objects.get(org=user.org,con=self.instance.file.con)
        if not (dealer in right.staff.all()):
            raise serializers.ValidationError("You can't assign a comment to non-staff.")
        return super().validate(attrs)
    def update(self, instance, validated_data):
        user = self.context['request'].user
        assign = super().update(instance, validated_data)
        if instance.dealer.mailbell.newmessage:
            send_celery( # send email
                "New comment to deal with",
                f"Hello, {instance.dealer.username}\n {user.username} has assigned you a new comment in the file {instance.file.name} to treat, with content as:\n {instance.text}",
                None,
                [instance.dealer.email],
                fail_silently=False,
            )
        return assign
class TreatCommentSerializer(serializers.ModelSerializer):
    # set comments to be treated in one 
    comments = PKRF(queryset=Comment.objects.all(),many=True)
    class Meta:
        model = File
        fields = ['id','comments']
        read_only_fields = ['id']
    def validate(self, attrs): # exclude the exterior comments
        list = self.instance.comments.all()
        for comment in attrs.get('comments',[]):
            if not comment in list:
                raise serializers.ValidationError("There are comments not to the file.")
        return super().validate(attrs)
    def update(self, instance, validated_data): # treat them
        comments = validated_data['comments'] 
        instance.is_commented = False
        list = instance.comments.all(is_treated=False)
        for comment in list:
            if comment in comments:
                comment.is_treated = True
                comment.save()
            else:
                instance.is_commented = True
        instance.save()
        return super().update(instance, validated_data)

# à installer, not used
class RaiseBoycottSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id','is_boycotted']
        read_only_fields = ['id','is_boycotted']
    def update(self, instance, validated_data):
        instance.is_boycotted = True
        instance.save()
        user = self.context['request'].user
        chief_principal = OrgConRight.objects.get(org=instance.exer.org,con=instance.con).chief
        send_celery(
            "New proposition against your template",
            f"Hello, {chief_principal.name}\n {user.username} has raised a proposition against the file {instance.name}.",
            None,
            [chief_principal.email],
            fail_silently=False,
        )
        return super().update(instance, validated_data)
    
# class SetChiefSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = OrgConRight
#         fields = ['id','chief']
#         read_only_fields = ['id','chief']
#     def update(self, instance, validated_data):
#         validated_data['chief'] = self.context['request'].user
#         return super().update(instance, validated_data)
