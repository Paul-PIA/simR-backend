from rest_framework import serializers
from rest_framework.serializers import PrimaryKeyRelatedField as PKRF
from django.utils import timezone 

from .models import CustomUser,Organization,Contract,Exercise,File,Comment,Share
from .models import FileAccess,MailBell
from .models import OrgConRight,OrgExerRight,UserExerRight

class ShareSerializer(serializers.ModelSerializer):
    from_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    to_user = PKRF(queryset=CustomUser.objects.all())
    file = PKRF(queryset=File.objects.all())
    class Meta:
        model = Share
        fields = '__all__'
        read_only_fields = ['id','from_user',]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None:
            self.fields['to_user'].read_only =True
            self.fields['date'].read_only =True
            self.fields['file'].read_only =True
            self.fields['between_org'].read_only =True
    def validate(self, attrs):
        attrs['from_user'] = self.context['request'].user
        if attrs.get('to_user',None) == attrs['from_user']:
            raise serializers.ValidationError("It's no use to share it to yourself.")
        if attrs.get('between_org',None):
            to_user = attrs['to_user']
            org = to_user.org
            if org == attrs['from_user'].org:
                raise serializers.ValidationError("It's no use to share it to your organization.")
            con = attrs['file'].con
            right = OrgConRight.objects.filter(con=con,org=org)
            if not right:
                raise serializers.ValidationError("This organizations isn't in the contract.")
            chief = right.first().chief
            if not chief:
                raise serializers.ValidationError("The chief hasn't validated.")
            if chief != to_user:
                raise serializers.ValidationError("Share between organizations must be to the certain chief.")
        return super().validate(attrs)
    def create(self, validated_data):
        file = validated_data['file']
        to_user = validated_data['to_user']
        access = FileAccess.objects.get(file=file)
        access.user.add(to_user)
        if validated_data.get('between_org',None):
            access.org.add(to_user.org)
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

def chiefrightcopy(user:CustomUser,exer:Exercise):
    right = OrgExerRight.objects.get(exer=exer,org=user.org)
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

class OrgConRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgConRight
        fields = '__all__'
        read_only_fields = ['id','org','con','is_principal','nb_access','chief']
    def validate_chief(self,value):
        if self.instance.chief is None and value is None:#locked before validation of chief
            raise serializers.ValidationError("The chief has not validated.")
        if self.instance.org != value.org:#chief relate to org
            raise serializers.ValidationError("Chief must be in the Organization.")
        if self.instance.chief and value:#chief is fixed
            raise serializers.ValidationError("Parameter chief is read-only once set.")
        else:
            return value
    def validate_staff(self,value):
        if len(value)>self.instance.nb_access:
            raise serializers.ValidationError("List of staff is too long.")
        if self.instance.chief not in value:#chief is staff
            raise serializers.ValidationError("Chief isn't in the staff.")
        for user in value:#staff is in the org
            if self.instance.org != user.org:
                raise serializers.ValidationError("Staff must be in the Organization.")
        return value
    def validate_nb_access(self,value):
        if value<len(self.instance.staff.all()):#number of access>number of staff
            raise serializers.ValidationError("Number of account can't be less than the number of staff.")
        con = self.instance.con
        sum = 0
        for org in con.org.all():
            if org != self.instance.org:
                sum += OrgConRight.objects.get(con=con,org=org).nb_access
        if value>con.nb_access-sum:#number of access<the number left
            raise serializers.ValidationError("Number of account is too big.")
        return value
    def update(self, instance, validated_data):
        chief = validated_data['chief']
        con = instance.con
        if chief:#chief validating, generate his rights
            validated_data['staff']= [chief,]
        staff_old = instance.staff.all()
        staff_new = validated_data['staff']
        for user in staff_old:#delete old relationship
            if not (user in staff_new):
                UserExerRight.objects.filter(user=user,exer__con=con).delete()
        for user in staff_new:#create new relationship
            if not (user in staff_old):
                for exer in con.exers.all():
                    UserExerRight.objects.create(user=user,exer=exer)
        for exer in con.exers.all():    
            chiefrightcopy(chief,exer)
        right = super().update(instance, validated_data)
        return right
# class UserConRightSerializer(serializers.ModelSerializer): #### will be abandonned
#     class Meta:
#         model = UserConRight
#         fields = '__all__'
#         read_only_fields = ['id','user','con','is_chief']
class OrgExerRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgExerRight
        fields = '__all__'
        read_only_fields = ['id','org','exer']
    def update(self, instance, validated_data):
        right = super().update(instance, validated_data)
        chief = OrgConRight.objects.get(org=instance.org,con=instance.exer.con).chief
        if chief:
            chiefrightcopy(chief,instance.exer)
        return right
class UserExerRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExerRight
        fields = '__all__'
        read_only_fields = ['id','user','exer']
    

class UserSerializer(serializers.ModelSerializer):
    org = PKRF(queryset=Organization.objects.all())
    mailbell = MailBellSerializer
    class Meta:
        model = CustomUser
        fields = '__all__'
        read_only_fields = ['id','date_joined','last_login','is_active','is_staff','is_superuser']
    def validate_org(self,value):
        if self.instance and self.instance.org and value:
            raise serializers.ValidationError("Parameter org is read-only once set.")
        else:
            return value
    def create(self, validated_data):
        user = super().create(validated_data)
        MailBell.objects.create(user=user)
        return user
class OrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ['id']
class ConSerializer(serializers.ModelSerializer):
    org_detail = OrgSerializer(source="org",many=True,read_only=True)
    org = PKRF(queryset=Organization.objects.all(),many=True,write_only=True)
    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = ['id',]
    def validate(self, attrs):
        if attrs.get('nb_org',None):
            nb_org = attrs['nb_org']
        else:
            nb_org = self.instance.nb_org
        if len(attrs['org']) > nb_org:
            raise serializers.ValidationError("List org is too long.")
        if self.instance is not None:
            org = OrgConRight.objects.filter(con=self.instance,is_principal=True).first().org
            if attrs['org'] is not None and org not in attrs['org']:
                raise serializers.ValidationError("The principal organization must be in.")
        return super().validate(attrs)
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['org']= data['org_detail']
        return data
    def create(self, validated_data):
        contract = super().create(validated_data)
        user = self.context['request'].user
        right = OrgConRight.objects.create(
            org=user.org,con=contract,is_principal=True,nb_access=1,
            chief=user,
        )
        orgs = contract.org.all()
        for org in orgs:
            if org != user.org:
                OrgConRight.objects.create(
                    org=org,con=contract,nb_access=1,
                )
        right.staff.set([user,])
        return contract
    def update(self, instance, validated_data):
        orgs_old = list(instance.org.all())
        orgs_new = validated_data['org']
        contract = super().update(instance, validated_data)
        for org in orgs_old:
            if not (org in orgs_new):
                UserExerRight.objects.filter(exer__con=contract,user__org=org).delete()
                OrgConRight.objects.filter(con=contract,org=org).delete()
                OrgExerRight.objects.filter(exer__con=contract,org=org).delete()
        for org in orgs_new:
            if not (org in orgs_old):
                OrgConRight.objects.create(con=contract,org=org,nb_access=1)
                for exer in contract.exers.all():
                    OrgExerRight.objects.create(exer=exer,org=org)
        return contract
class ExerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'
        read_only_fields = ['id','org']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None:
            self.fields['con','org',].read_only =True
    def validate_org(self,value):
        user = self.context['request'].user
        if user.org != value:
            raise serializers.ValidationError("You're not in the organization.")
        return value
    def validate(self, attrs):
        user = self.context['request'].user
        if not OrgConRight.objects.filter(org=user.org,con=attrs['con']):
            raise serializers.ValidationError("Your organization isn't a member of this contract.")
        data = attrs
        data['org'] = user.org
        return super().validate(data)
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['org']=user.org
        exercise = super().create(validated_data)
        contract = validated_data['con']
        orgs = contract.org.all()
        for _org in orgs:
            if _org == user.org:
                OrgExerRight.objects.create(
                    org=_org,exer=exercise,role='A',
                    input=True,output=True,graph=True,
                    rewrite=True,comment=True,download=True,share=True,
                )
            else:
                OrgExerRight.objects.create(org=_org,exer=exercise)
            users = OrgConRight.objects.get(org=_org,con=contract).staff.all()
            for _user in users:
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
    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['id','last_update','is_locked','is_commented','is_boycotted','is_final','is_public']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance is not None:
            self.fields['uploader'].read_only = True
            self.fields['con'].read_only = True
            self.fields['exer'].read_only = True
            self.fields['is_template'].read_only =  True
    def validate(self, attrs):
        if attrs.get('exer',None):
            if attrs['exer'].con != attrs['con']:
                raise serializers.ValidationError("The exercise isn't in the contract.")
        return super().validate(attrs)
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['uploader'] = user
        file = super().create(validated_data)
        access = FileAccess.objects.create(file=file)
        access.user.add(user)
        access.org.add(user.org)
        return file
    def update(self, instance, validated_data):
        file = super().update(instance, validated_data)
        file.last_update = timezone.now()
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
    def create(self, validated_data):
        file = validated_data['file']
        file.is_commented = True
        return super().create(validated_data)

# Special RETRIEVE: Spaces
class SpaceShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = ['file']

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAccess
        fields = ['file']

#Special UPDATE:

# class TestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Contract
#         fields = '__all__'
    # def create(self, validated_data):
    #     org_name = validated_data.pop('org')
    #     name = validated_data.pop('name')
    #     nb_org = validated_data.pop('nb_org')
    #     nb_access = validated_data.pop('nb_access')
    #     filter = Organization.objects.filter(name=org_name)
    #     if not filter:
    #         org = Organization.objects.create(name=org_name,adrs="wenzhou",tel="9",post="6")
    #     con = Contract.objects.create(org=org,name=name,nb_org=nb_org,nb_access=nb_access)
    #     return con