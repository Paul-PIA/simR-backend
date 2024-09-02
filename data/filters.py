from django_filters import rest_framework as filters

from .models import CustomUser,Organization,Contract,Exercise,File,Comment,Invitation,Notification
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserExerRight

#searchable models
#All that can be set: exact,iexact,contains,icontains,in,gt,gte,lt,lte,startswith,istartswith,endswith,iendswith
class UserFilter(filters.FilterSet):
    class Meta:
        model = CustomUser
        fields = {
            'id':['exact','lt','gt'],
            'username':['exact','icontains'],
            'first_name':['exact','icontains'],
            'last_name':['exact','icontains'],
            'org':['exact','in'],
        }
class OrgFilter(filters.FilterSet):
    class Meta:
        model = Organization
        fields = {
            'id':['exact','lt','gt'],
            'name':['exact','icontains'],
            'cons__name':['exact','icontains'],
        }
class ConFilter(filters.FilterSet):
    class Meta:
        model = Contract
        fields = {
            'id':['exact','lt','gt'],
            'name':['exact','icontains'],
            'org__name':['exact','icontains'],
        }
class ExerFilter(filters.FilterSet):
    class Meta:
        model = Exercise
        fields = {
            'id':['exact','lt','gt'],
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
            'is_template':['exact'],
        }
class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = {
            'id':['exact','lt','gt'],
            'file':['exact','in'],
            'commenter':['exact','in'],
            'dealer':['exact','in'],
            'is_treated':['exact',],
        }

class NotificationFilter(filters.FilterSet):
    class Meta:
        model = Notification
        fields = {
            'id':['exact','lt','gt'],
            'actor':['exact','in'],
            'trigger_time':['exact','in'],
            'object':['exact','in'],
            'event':['exact','in'],
        }

class OrgConFilter(filters.FilterSet):
    class Meta:
        model = OrgConRight
        fields = {
            'org':['exact',],
            'con':['exact',],
        }
class OrgExerFilter(filters.FilterSet):#Useless
    class Meta:
        model = OrgExerRight
        fields = {
            'org':['exact',],
            'exer':['exact',],
        }
class UserExerFilter(filters.FilterSet):
    class Meta:
        model = UserExerRight
        fields = {
            'user':['exact',],
            'exer':['exact',],
        }

class ShareFilter(filters.FilterSet):
    class Meta:
        model = Share
        fields = {
            'from_user':['exact',],
            'to_user':['exact',],
            'file':['exact',],
        }