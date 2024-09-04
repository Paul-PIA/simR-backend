# from django.shortcuts import render,get_object_or_404
from django.db import models
from django.utils.timezone import now
from django.http import HttpResponse,Http404
from django.core.exceptions import ObjectDoesNotExist as ODNE

from rest_framework import viewsets,views
from rest_framework.response import Response
from rest_framework import permissions,status

from allauth.account.forms import ResetPasswordForm
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import CustomUser,Organization,Contract,Exercise,File,Comment,Invitation,Notification
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserExerRight

import data.serializers as serializers
from .serializers import SpaceShareSerializer,SpaceSerializer,PrintCommentSerializer
from .serializers import SetFileStateSerializer,SetUserStateSerializer,AssignCommentSerializer,TreatCommentSerializer
from .serializers import DistributeAccountSerializer,RaiseBoycottSerializer,chiefrightcopy

import data.filters as filters

from .permissions import IsPrincipalAndChief as IPAC,IsChief as IC,IsSelf as IS
from .permissions import CanDo as CD, IsOtherChief as IOF
# from django.template import loader
from .tasks import send_notification,add

#views
def index(request):
    return HttpResponse("Here drops the principal homepage.")
# small click
def trigger(request):
    for i in [0,1,2,3,4,5,6]:
        print(add.delay(i,i))
    return HttpResponse("Finished.")
def trigger_fidele(request):
    for i in [0,1,2,3,4,5,6]:
        add(i,i)
    return HttpResponse("Finished.")

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.select_related('org').all()
    serializer_class = serializers.UserSerializer
    filterset_class = filters.UserFilter
    ordering_fields = ["id",]
    def create(self,request,*args,**kwargs): # abandonned
        return Response({"detail":"Creating users via this API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update','destroy']:
            permission_classes = [IS]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [per() for per in permission_classes]
class OrgViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.prefetch_related('cons').all()
    serializer_class = serializers.OrgSerializer
    filterset_class = filters.OrgFilter
    ordering_fields = ["id",]
    def get_permissions(self):
        if self.action in ['create','update','partial_update','destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [per() for per in permission_classes]
class ConViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.prefetch_related('org').all()
    serializer_class = serializers.ConSerializer
    filterset_class = filters.ConFilter
    ordering_fields = ["id",]
    def get_permissions(self):
        if self.action in ['create','destroy','list','retrieve']:
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ['update','partial_update']:
            permission_classes = [IPAC]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [per() for per in permission_classes]
    def update(self, request, *args, **kwargs): 
        ### get receiver
        instance = self.get_object()
        org = instance.org.all()
        right = OrgConRight.objects.prefetch_related('staff').filter(con=instance,org__in=org)
        staff = right.values_list('staff',flat=True)
        for user in staff:
            print(user)
        receiver = CustomUser.objects.select_related('org').prefetch_related(
            models.Prefetch("con_staff",queryset=right,to_attr="_right")
        )
        for user in receiver:
            print(user.__str__(),user._right)
        ### update
        response = super().update(request, *args, **kwargs)
        trigger_time = now()
        ### send notification
        self.sender(request,response,trigger_time,receiver)
        return response
    def sender(self,request,response,trigger_time,receiver): # when change the list of orgs
        if response.status_code == 200:
            instance = self.get_object()
            org_new = instance.org.all()
            user_remain = receiver.filter(org__in=org_new).values_list('id',flat=True)
            user_removed = receiver.exclude(org__in=org_new).values_list('id',flat=True)
            message_remain = f"{request.user.username} has shaken up the organizations in the contract {instance.name}."
            send_notification.delay(
                receiver = user_remain,#list of ids
                actor = request.user.id, # id
                message = message_remain,event = 'U',object = 'T',
                trigger_time = trigger_time
            )
            message_removed = f"Your organization has been removed from the contract {instance.name}."
            send_notification.delay(
                receiver = user_removed,
                actor = request.user.id,
                message = message_removed,event = 'D',object = 'T',
                trigger_time = trigger_time
            )
class ExerViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.select_related('con').prefetch_related('user_rights__user').all()
    serializer_class = serializers.ExerSerializer
    filterset_class = filters.ExerFilter
    ordering_fields = ["id","date_i","date_f"]
    def get_permissions(self):
        if self.action in ['create','update','partial_update','destroy']:
            permission_classes = [IC]
        elif self.action in ['list','retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(user_rights__user=user)
    def create(self, request, *args, **kwargs): 
        response = super().create(request, *args, **kwargs)
        trigger_time = now()
        self.sender(request,response,trigger_time)
        return response
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        trigger_time = now()
        self.sender(request,response,trigger_time)
        return response
    def sender(self,request,response,trigger_time): # create notification for C,U
        if response.status_code == 201:
            message = f"{request.user.username} has created the exercise {instance.name}."
        if response.status_code == 200:
            message = f"{request.user.username} has updated the work time of the exercise {instance.name}."
        instance = self.get_object()
        rights = OrgConRight.objects.select_related('chief').filter(con=instance.con)
        chiefs = [right.chief.id for right in rights]
        send_notification.delay(
            receiver = chiefs, # list of ids
            actor = request.user.id, # id
            message = message,event = 'C',object = 'E',
            trigger_time = trigger_time
        )
    
class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.select_related('uploader','con','exer','access').prefetch_related('access__user').all()
    serializer_class = serializers.FileSerializer
    filterset_class = filters.FileFilter
    ordering_fields = ["id","last_update",]
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        trigger_time = now()
        self.sender(request,response,trigger_time,name=None)
        return response
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        trigger_time = now()
        self.sender(request,response,trigger_time,name=None)
        return response
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        file = File.objects.select_related('exer','con','uploader__org').get(id=obj.id)
        right = OrgConRight.objects.select_related('chief').get(org=file.uploader.org,con=file.con)
        name = [obj.name,obj.exer.name,right.chief.id]
        response = super().destroy(request, *args, **kwargs)
        trigger_time = now()
        self.sender(request,response,trigger_time,name=name)
        return response
    def get_permissions(self):
        if self.action in ['update','partial_update','destroy']:
            permission_classes = [CD]
        elif self.action in ['create']:
            permission_classes = [IS]
        elif self.action in ['list','retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(access__user=user)
    def sender(self,request,response,trigger_time,name):
        if response.status_code in [201,200]:
            instance = self.get_object()
            file = File.objects.select_related('exer','con','uploader__org').get(id=instance.id)
            right = OrgConRight.objects.select_related('chief').get(org=file.uploader.org,con=file.con)
            id = right.chief.id
            if response.status_code == 200:# update a file
                event = 'C'
                message = f"{request.user.username} has updated the file {file.name} in exercise {file.exer.name}."
            else:# upload a file
                event = 'U'
                message = f"{request.user.username} has uploaded the file {file.name} in exercise {file.exer.name}."
        if response.status_code == 204:# delete a file
            message = f"{request.user.username} has deleted the file {name[0]} in exercise {name[1]}."
            id = name[2]
            event = 'D'
        if response.status_code in [201,200,204]:
            send_notification.delay(
                receiver = [id], # list of ids
                actor = request.user.id, # id
                message = message,event = event,object = 'F',
                trigger_time = trigger_time
            )

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('file','commenter','dealer').prefetch_related('file__access__user').all()
    serializer_class = serializers.CommentSerializer
    filterset_class = filters.CommentFilter
    ordering_fields = ["id",]
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        trigger_time=now()
        self.sender(request,response,trigger_time)
        return response
    def destroy(self, request, *args, **kwargs):
        file = self.get_object().file
        action = super().destroy(request, *args, **kwargs)
        file.is_commented = False
        comments = file.comments.all()
        for comment in comments:
            if not comment.is_treated:
                file.is_commented = True
        file.save()
        return action
    def get_permissions(self):
        if self.action in ['update','partial_update','destroy']:
            permission_classes = [IS]
        elif self.action in ['create']:
            permission_classes = [CD]
        elif self.action in ['list','retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(file__access__user=user)
    def sender(self,request,response,trigger_time):# make a comment
        if response.status_code == 201:
            instance = self.get_object()
            file = File.objects.select_for_update('exer','org','exer__con').get(id=instance.file.id)
            message = f"{request.user.username} has commented the file {file.name} in exercise {file.exer.name}."
            chief = OrgConRight.objects.select_related('chief').get(org=file.exer.org,con=file.con).chief
            send_notification.delay(
                receiver = [chief.id], # list of ids
                actor = request.user.id, # id
                message = message,event = 'C',object = 'M',
                trigger_time = trigger_time
            )

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related('actor').all()
    serializer_class = serializers.NotificationSerializer
    filterset_class = filters.NotificationFilter
    ordering_fields = ["id",'trigger_time']
    permission_classes = [permissions.IsAuthenticated]
    def create(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Creating access to file via API is not allowed."})
    def update(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Updating access to file via API is not allowed."})
    def destroy(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Deleting access to file via API is not allowed."})
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(receiver=user)

#rights
class MailBellViewSet(viewsets.ModelViewSet):
    queryset = MailBell.objects.all()
    serializer_class = serializers.MailBellSerializer
    permission_classes = [IS]
    def create(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Creating mail bell via API is not allowed."})
    def destroy(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Deleting mail bell via API is not allowed."})
    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user=user)

class ShareViewSet(viewsets.ModelViewSet):
    queryset = Share.objects.select_related('from_user','to_user','file').all()
    serializer_class = serializers.ShareSerializer
    filterset_class = filters.ShareFilter
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        trigger_time=now()
        self.sender(request,response,trigger_time)
        return response
    def destroy(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Deleting share record via API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update']:
            permission_classes = [IS]
        elif self.action in ['create']:
            permission_classes = [CD]
        elif self.action in ['list','retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(models.Q(to_user=user)|models.Q(from_user=user))
    def sender(self,request,response,trigger_time):# share a file
        if response.status_code == 201:
            instance = self.get_object()
            to_user = instance.to_user
            file = instance.file
            exer = file.exer
            con = file.con
            message_chief = f"{request.user.username} has shared the file {file.name} in the Exercise {exer.name} to {to_user.username} of Organization {to_user.org.name}."
            message_to = f"{request.user.username} has shared the file {file.name} in the Exercise {exer.name} to you."
            chief = OrgConRight.objects.select_related('chief').get(con=con,org=request.user.org).chief
            send_notification.delay(
                receiver = [chief.id],#list of ids
                actor = request.user.id, # id
                message = message_chief,event = 'S',object = 'F',
                trigger_time = trigger_time
            )
            send_notification.delay(
                receiver = [to_user.id],#list of ids
                actor = request.user.id, # id
                message = message_to,event = 'S',object = 'F',
                trigger_time = trigger_time
            )

class FileAccessViewSet(viewsets.ModelViewSet):
    queryset = FileAccess.objects.all()
    serializer_class = serializers.FileAccessSerializer
    permission_classes = [permissions.IsAdminUser]
    def create(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Creating access to file via API is not allowed."})
    def update(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Updating access to file via API is not allowed."})
    def destroy(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Deleting access to file via API is not allowed."})
    
class OrgConRightViewSet(viewsets.ModelViewSet):
    queryset = OrgConRight.objects.select_related('org').select_related('con').prefetch_related('staff').all()
    serializer_class = serializers.OrgConRightSerializer
    filterset_class = filters.OrgConFilter
    def create(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Creating the right via API is not allowed."})
    def update(self, request, *args, **kwargs):# change staff
        staff_old = list(self.get_object().staff.all())
        response = super().update(request, *args, **kwargs)
        trigger_time=now()
        self.sender(request,response,trigger_time,staff_old)
        return response
    def destroy(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Deleting the right via API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update']: # change staff
            permission_classes = [IC]
        elif self.action in ['list','retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(staff=user)
    def sender(self,request,response,trigger_time,staff_old):# change staff
        if response.status_code == 200:
            instance = self.get_object()
            staff_new = instance.staff.all()
            staff_remain = []
            staff_removed = []
            for staff in staff_old:
                if staff in staff_new:
                    staff_remain.append(staff.id)
                else:
                    staff_removed.append(staff.id)
            print(staff_remain,staff_removed)
            message_remain = f"{request.user.username} has updated the team of {instance.org.name} in the contract {instance.con.name}."
            message_removed = f"You have been removed from the team of {instance.org.name} in the contract {instance.con.name}."
            send_notification.delay(
                receiver = staff_remain,#list of ids
                actor = request.user.id, # id
                message = message_remain,event = 'U',object = 'T',
                trigger_time = trigger_time
            )
            if len(staff_removed)>0:
                send_notification.delay(
                    receiver = staff_removed,#list of ids
                    actor = request.user.id, # id
                    message = message_removed,event = 'D',object = 'T',
                    trigger_time = trigger_time
                )
class OrgExerRightViewSet(viewsets.ModelViewSet):
    queryset = OrgExerRight.objects.all()
    serializer_class = serializers.OrgExerRightSerializer
    filterset_class = filters.OrgExerFilter
    def create(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Creating the right via API is not allowed."})
    def destroy(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Deleting the right via API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update']:
            permission_classes = [IC]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
class UserExerRightViewSet(viewsets.ModelViewSet):
    queryset = UserExerRight.objects.select_related('user','exer').prefetch_related('user__org').all()
    serializer_class = serializers.UserExerRightSerializer
    filterset_class = filters.UserExerFilter
    def create(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Creating the right via API is not allowed."})
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        trigger_time = now()
        self.sender(request,response,trigger_time)
        return response
    def destroy(self, request, *args, **kwargs): # abandonned
        return Response({"detail":"Deleting the right via API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update']:
            permission_classes = [IC]
        elif self.action in ['list','retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            exers = UserExerRight.objects.filter(user=user).values_list('exer',flat=True)
            return self.queryset.filter(exer__in=exers,user__org=user.org)
    def sender(self,request,response,trigger_time):# update right
        if response.status_code == 200:
            instance = self.get_object()
            message = f"Your right in exercise {instance.exer.name} is reset."
            send_notification.delay(
                receiver = [instance.user.id],#list of ids
                actor = request.user.id, # id
                message = message,event = 'U',object = 'R',
                trigger_time = trigger_time
            )

# Don't use this
# class InvitationViewSet(viewsets.ModelViewSet):
#     queryset = Invitation.objects.all()
#     serializer_class = serializers.InvitationSerializer
#     permission_classes = [permissions.AllowAny]
#     def update(self, request, *args, **kwargs): # abandonned
#         return Response({"detail":"Updating access to file via API is not allowed."})
#     def destroy(self, request, *args, **kwargs): # abandonned
#         return Response({"detail":"Deleting mail bell via API is not allowed."})
#     def get_queryset(self):
#         user = self.request.user
#         return self.queryset.filter(inviter=user)

# Certain getters, abandonned
def str_to_bool(s):
    if s.lower() in ['1','True','true','T','t','Yes','yes','Y','y']:
        return True
    else:
        return False

class MySpaceShareView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        exer = request.query_params.get('exer',None)
        to_me = str_to_bool(request.query_params.get('to_me',''))
        from_me = str_to_bool(request.query_params.get('from_me',''))
        if exer:
            if to_me and from_me:
                return Response({"message":"Parameter to_me XOR from_me is required."},status=status.HTTP_400_BAD_REQUEST)
            elif not (to_me or from_me):
                return Response({"message":"Parameter to_me XOR from_me is required."},status=status.HTTP_400_BAD_REQUEST)
            else:
                if to_me:
                    queryset = Share.objects.filter(to_user=request.user,file__exer=exer)
                else:
                    queryset = Share.objects.filter(from_user=request.user,file__exer=exer)
                serializer = SpaceShareSerializer(queryset.order_by('-date').distinct(),many=True)
            return Response(serializer.data)
        else:
            return Response({"message":"Parameter exer is required."},status=status.HTTP_400_BAD_REQUEST)
class MySpaceView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request,*args,**kwargs):
        exer = request.query_params.get('exer',None)
        if exer:
            queryset = File.objects.filter(exer=exer,access__user=request.user)
            serializer = SpaceSerializer(queryset.order_by('-last_update'),many=True)
            return Response(serializer.data)
        else:
            return Response({"message":"Parameter exer is required."})
class MyOrgSpaceView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request,*args,**kwargs):
        exer = request.query_params.get('exer',None)
        is_template = str_to_bool(request.query_params.get('is_template',''))
        org = request.user.org
        if exer:
            if is_template:
                file = File.objects.filter(is_template=True,access__org=org)
            else:
                file = File.objects.filter(org=org)
            serializer = SpaceSerializer(file,many=True)
            return Response(serializer.data)
        else:
            return Response({"message":"Parameter exer is required."})
class PublicSpaceView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request,*args,**kwargs):
        exer = request.query_params.get('exer',None)
        is_template = str_to_bool(request.query_params.get('is_template',''))
        org = request.user.org
        if not exer:
            return Response({"message":"Parameter exer is required."})
        if is_template:
            file = File.objects.filter(is_template=True,exer=exer)
            file = exer.files.all().filter(is_template=True)
        else:
            file = File.objects.filter(is_public=True,exer=exer,org=org)
        serializer = SpaceSerializer(file,many=True)
        return Response(serializer.data)
class PrintCommentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request,*args,**kwargs):
        id = request.query_params.get('file_id',None)
        if not id:
            return Response({"message":"Parameter file_id is required."})
        file = File.objects.get(id=id)
        comments = file.comments.all().order_by('-time')
        serializer = PrintCommentSerializer(comments,many=True)
        return Response(serializer.data)

# LOCK it in the real server, to set the first administer
class AdamView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(
        operation_id="set_superuser",
        description="Set the first superuser",
        parameters=[
            OpenApiParameter(
                name='Authorization',
                description='JWT token',
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER
            )
        ],
        responses={
            200: OpenApiTypes.OBJECT(
                properties={
                    'message': OpenApiTypes.STR
                }
            ),
            400: OpenApiTypes.OBJECT(
                properties={
                    'error': OpenApiTypes.STR
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        user=request.user
        if len(list(CustomUser.objects.all()))==1 and not (user.is_superuser and user.is_staff):
            user.is_superuser=True
            user.is_staff=True
            user.save()
            return Response({"message":f"Hello, Adam."},status=status.HTTP_200_OK)
        else:
            return Response({"message":f"This API is sealed. Go to ask the superuser for your permission."},status=status.HTTP_400_BAD_REQUEST)

# Certain evaluaters
class SetUserStateView(views.APIView):
    permission_classes = [permissions.IsAdminUser]
    @extend_schema(
        operation_id="set_user_state",
        description="Set a user's state in the system",
        parameters=[
            OpenApiParameter(name='Authorization',description='JWT token',required=True,type=OpenApiTypes.STR,location=OpenApiParameter.HEADER)
        ],
        request={
            'application/json': OpenApiTypes.OBJECT(
                properties={
                    'is_active':OpenApiTypes.BOOL,'is_staff':OpenApiTypes.BOOL,'is_superuser':OpenApiTypes.BOOL
                },
                required=[]
            )
        },
        responses={
            200: OpenApiTypes.OBJECT(
                properties={
                    'message': OpenApiTypes.STR,
                    'data': OpenApiTypes.OBJECT(
                        properties={
                            'is_active':OpenApiTypes.BOOL,'is_staff':OpenApiTypes.BOOL,'is_superuser':OpenApiTypes.BOOL
                        }
                    )
                }
            ),
            400: OpenApiTypes.OBJECT(
                properties={
                    'error': OpenApiTypes.STR
                }
            )
        }
    )
    def get_object(self,pk):
        try:
            return CustomUser.objects.get(id=pk)
        except CustomUser.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None): # update
        obj = self.get_object(pk)
        serializer = SetUserStateSerializer(instance=obj,data=request.data,partial=True,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            trigger_time = now()
            self.sender(self,request,obj,trigger_time)
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    def sender(self,request,obj,trigger_time):
        if obj.is_staff:
            _message = "You have been set to be the administer."
        else:
            _message = "You have been set not to be the administer."
        send_notification.delay(
            receiver = [obj.id],
            actor = request.user.id,
            message = _message,event = 'U',object = 'U',
            trigger_time = trigger_time
        )
class SetFileStateView(views.APIView):
    permission_classes = [IC]
    def get_object(self,pk):
        try:
            return File.objects.get(id=pk)
        except File.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None): # update
        obj = self.get_object(pk)
        self.check_object_permissions(request,obj)
        serializer = SetFileStateSerializer(instance=obj,data=request.data,partial=True,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            trigger_time = now()
            state = request.data.get('is_public',None)
            if state:
                self.sender(request,obj,trigger_time)
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    def sender(self,request,obj,trigger_time):
        _message = f"{request.user.username} has published the file {obj.name}."
        send_notification.delay(
            receiver = obj.dealer.id,
            actor = request.user.id,
            message = _message,event = 'U',object = 'C',
            trigger_time = trigger_time
        )
        rights = OrgConRight.objects.select_related('chief').filter(con=obj.con)
        user = []
        for right in rights:
            if right.chief is not None:
                user.append(right.chief.id)

class DistributeAccountView(views.APIView):
    permission_classes = [IPAC]
    def get_object(self,pk):
        try:
            return Contract.objects.get(id=pk)
        except Contract.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None): # update
        obj = self.get_object(pk)
        self.check_object_permissions(request,obj)
        serializer = DistributeAccountSerializer(instance=obj,data=request.data,partial=True,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            trigger_time=now()
            self.sender(request,obj,trigger_time)
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    def sender(self,request,obj,trigger_time):
        _message = f"{request.user.username} has distributed the max number of accounts in your team in the contract {obj.name}."
        rights = OrgConRight.objects.select_related('chief').filter(con=obj)
        user = []
        for right in rights:
            if right.chief is not None:
                user.append(right.chief.id)
        send_notification.delay(
            receiver = user,
            actor = request.user.id,
            message = _message,event = 'U',object = 'T',
            trigger_time = trigger_time
        )

class AssignCommentView(views.APIView):
    permission_classes = [IC]
    def get_object(self,pk):
        try:
            return Comment.objects.get(id=pk)
        except Comment.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None):
        obj = self.get_object(pk)
        self.check_object_permissions(request,obj)
        serializer = AssignCommentSerializer(instance=obj,data=request.data,partial=True,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            trigger_time = now()
            self.sender(request,obj,trigger_time)
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    def sender(self,request,obj,trigger_time):
        _message = f"{request.user.username} has assigned you a new comment in the file {obj.file.name} to treat."
        send_notification.delay(
            receiver = obj.dealer.id,
            actor = request.user.id,
            message = _message,event = 'U',object = 'C',
            trigger_time = trigger_time
        )
class TreatCommentView(views.APIView):
    permission_classes = [IC]
    def get_object(self,pk):
        try:
            return File.objects.get(id=pk)
        except File.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None):
        obj = self.get_object(pk)
        self.check_object_permissions(request,obj)
        serializer = TreatCommentSerializer(instance=obj,data=request.data,partial=True,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class SetChiefView(views.APIView):
    # a user invited to set as a chief
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self,pk):
        try:
            return OrgConRight.objects.select_related('con','org').get(id=pk)
        except OrgConRight.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None):
        token = request.query_params.get('token')
        obj = self.get_object(pk)
        user = request.user
        if obj.org != user.org:
            return Response({'error':'You are not in this organization.'},status=status.HTTP_403_FORBIDDEN)
        try:
            invitation = Invitation.objects.get(token=(token+str(pk)))
            if invitation.is_used or invitation.is_expired():
                return Response({'error':'Invitation token is used or expired.'},status=status.HTTP_400_BAD_REQUEST)
            obj.chief = user
            obj.save()
            obj.staff.set([request.user,])
            exers = Exercise.objects.filter(con=obj.con)
            for exer in exers:
                UserExerRight.objects.create(user=user,exer=exer)
                chiefrightcopy(user,exer,request.user)
            invitation.is_used = True
            invitation.save()
            trigger_time=now()
            self.sender(request,obj,trigger_time)
            return Response({'message':'You have participated in the contract.'},status=status.HTTP_200_OK)
        except Invitation.DoesNotExist: 
            return Response({'error':'Invalid invitation token.'},status=status.HTTP_404_NOT_FOUND)
    def sender(self,request,obj,trigger_time):
        _message = f"{request.user.username} has registered to be the chief of {obj.org.name} in the contract {obj.con.name}."
        rights = OrgConRight.objects.select_related('chief').filter(con=obj.con)
        user = []
        for right in rights:
            if right.chief is not None:
                user.append(right.chief.id)
        send_notification.delay(
            receiver = user,
            actor = request.user.id,
            message = _message,event = 'U',object = 'T',
            trigger_time = trigger_time
        )

class ResetPasswordConfirmView(views.APIView):
    def post(self,request):
        uid = request.data.get('uid',None)
        token = request.data.get('token',None)
        pwd = request.data.get('new_password',None)
        try:
            id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(id=id)
        except (TypeError,ValueError,OverflowError,CustomUser.DoesNotExist):
            return Response({'error':'Invalid request.'},status=status.HTTP_400_BAD_REQUEST)
        if default_token_generator(user,token):
            if pwd != request.data.get('repeat_new_password',None):
                return Response({'error':'The new passwords don\'t match.'},status=status.HTTP_400_BAD_REQUEST)
            else:
                user.set_password(pwd)
                user.save()
                trigger_time=now()
                self.sender(request,user,trigger_time)
                return Response({'message':'You have reset your password.'},status=status.HTTP_200_OK)
        else:
            return Response({'error':'Invalid token or uid.'},status=status.HTTP_400_BAD_REQUEST)        
    def sender(self,request,obj,trigger_time):
        _message = f"You have reset your account password."
        user = []
        user.append(obj.id)
        send_notification.delay(
            receiver = user,
            actor = obj.id,
            message = _message, event = 'U',object = 'U',
            trigger_time = trigger_time
        )

#not used
class RaiseBoycottView(views.APIView):
    permission_classes = [IOF]
    def get_object(self,pk):
        try:
            return File.objects.get(id=pk)
        except File.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None):
        obj = self.get_object(pk)
        self.check_object_permissions(request,obj)
        serializer = RaiseBoycottSerializer(instance=obj,data=request.data,partial=True,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

#Certain poster
class InviteChiefView(views.APIView):
    permission_classes = [IPAC|permissions.IsAdminUser]
    def get_object(self,pk):
        try:
            return Contract.objects.get(id=pk)
        except Contract.DoesNotExist:
            raise Http404
    def post(self,request,pk,format=None):
        obj = self.get_object(pk)
        self.check_object_permissions(request,obj)
        orgs = Organization.objects.filter(con_rights__con=obj,con_rights__chief=None)
        for org in orgs:
            email = request.data.get(str(org.pk),None)
            if email is None: # refuse the request if all positions aren't provided 
                return Response("Please fill in all the emails of chief.",status=status.HTTP_400_BAD_REQUEST)
        for org in orgs:
            email = request.data.get(str(org.pk))
            request.data['email'] = email
            serializer = serializers.InvitationSerializer(instance=None,data=request.data,context={"request":request}) # generate an invitation
            if serializer.is_valid():
                serializer.save()
                right = OrgConRight.objects.get(con=obj,org=org) 
                serializer.instance.send(right) # send email
                serializer.instance.token = serializer.instance.token + str(right.id) # enhence the quality of token
                serializer.instance.save()
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response("Invitation emails have been sent.",status=status.HTTP_200_OK)
    
class ForgotPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def post(self,request):
        form = ResetPasswordForm(data=request.data)
        if form.is_valid():
            form.save(request=request)
            return Response({'status':'ok'},status=status.HTTP_200_OK)
        return Response(form.errors,status=status.HTTP_400_BAD_REQUEST)