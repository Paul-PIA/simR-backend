from django_filters import rest_framework as filters

from .models import CustomUser,Organization,Contract,Exercise,File,Comment
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserConRight,UserExerRight

#exact,iexact,contains,icontains,in,gt,gte,lt,lte,startswith,istartswith,endswith,iendswith
class UserFilter(filters.FilterSet):
    class Meta:
        model = CustomUser
        fields = {
            'id':['lt','gt'],
            'username':['exact','icontains'],
            'first_name':['exact','icontains'],
            'last_name':['exact','icontains'],
            'org':['exact','in'],
        }

class OrgFilter(filters.FilterSet):
    class Meta:
        model = Organization
        fields = {
            'id':['lt','gt'],
            'name':['exact','icontains'],
            'cons':['exact','in'],
        }

class ConFilter(filters.FilterSet):
    class Meta:
        model = Contract
        fields = {
            'id':['lt','gt'],
            'name':['exact','icontains'],
        }

class ExerFilter(filters.FilterSet):
    class Meta:
        model = Exercise
        fields = {
            'id':['lt','gt'],
            'name':['exact','icontains'],
            'con':['exact','in'],
            'type':['exact'],
        }

class FileFilter(filters.FilterSet):
    class Meta:
        model = File
        fields = {
            'id':['lt','gt'],
            'name':['exact','icontains'],
            'uploader':['exact','in'],
            'con':['exact','in'],
            'exer':['exact','in'],
            'is_template':[],
        }

class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = {
            'id':['lt','gt'],
            'file':['exact','in'],
            'dealer':['exact','in'],
            'is_treated':[],
        }

class OrgConFilter(filters.FilterSet):
    class Meta:
        model = OrgConRight
        fields = {
            'org':[],
            'con':[],
        }
class UserConFilter(filters.FilterSet):
    class Meta:
        model = UserConRight
        fields = {
            'user':[],
            'con':[],
        }
class OrgExerFilter(filters.FilterSet):
    class Meta:
        model = OrgExerRight
        fields = {
            'org':[],
            'exer':[],
        }
class UserExerFilter(filters.FilterSet):
    class Meta:
        model = UserExerRight
        fields = {
            'user':[],
            'exer':[],
        }