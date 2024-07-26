# from django.shortcuts import render,get_object_or_404
from django.db import models
from django.utils.timezone import now
from django.http import HttpResponse,Http404
from django.core.exceptions import ObjectDoesNotExist as ODNE
from rest_framework import viewsets,views
from rest_framework.response import Response
from rest_framework import permissions,status

from .models import CustomUser,Organization,Contract,Exercise,File,Comment,Invitation
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserExerRight

from .serializers import UserSerializer,OrgSerializer,ConSerializer,ExerSerializer,FileSerializer,CommentSerializer,InvitationSerializer
from .serializers import MailBellSerializer,FileAccessSerializer,ShareSerializer
from .serializers import OrgConRightSerializer,OrgExerRightSerializer,UserExerRightSerializer
from .serializers import SpaceShareSerializer,SpaceSerializer,PrintCommentSerializer
from .serializers import SetFileStateSerializer,SetUserStateSerializer,RaiseBoycottSerializer,DistributeAccountSerializer,AssignCommentSerializer,TreatCommentSerializer
from .serializers import chiefrightcopy

from .filters import UserFilter,OrgFilter,ConFilter,ExerFilter,FileFilter,CommentFilter
from .filters import OrgConFilter,OrgExerFilter,UserExerFilter,ShareFilter

from .permissions import IsPrincipalAndChief as IPAC,IsChief as IC,IsSelf as IS
from .permissions import CanDo as CD, IsOtherChief as IOF
# from django.template import loader
from .tasks import send_notification  #,add

#views
def index(request):
    return HttpResponse("Here drops the principal homepage.")
#small click
# def trigger(request):
#     for i in [0,1,2,3,4,5,6]:
#         print(add.delay(i,i))
#     return HttpResponse("Finished.")
# def trigger_fidele(request):
#     for i in [0,1,2,3,4,5,6]:
#         add(i,i)
#     return HttpResponse("Finished.")

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.select_related('org').all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    ordering_fields = ["id",]
    def create(self,request,*args,**kwargs): 
        return Response({"detail":"Creating users via this API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update','destroy']:
            permission_classes = [IS]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [per() for per in permission_classes]
class OrgViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.prefetch_related('cons').all()
    serializer_class = OrgSerializer
    filterset_class = OrgFilter
    ordering_fields = ["id",]
    # def get_permissions(self):
    #     if self.action in ['create','update','partial_update','destroy']:
    #         permission_classes = [permissions.IsAdminUser]
    #     else:
    #         permission_classes = [permissions.IsAuthenticated]
    #     return [per() for per in permission_classes]
class ConViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.prefetch_related('org').all()
    serializer_class = ConSerializer
    filterset_class = ConFilter
    ordering_fields = ["id",]
    def get_permissions(self):
        if self.action in ['create','destroy']:
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
    def sender(self,request,response,trigger_time,receiver): # change orgs
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
    serializer_class = ExerSerializer
    filterset_class = ExerFilter
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
            receiver = chiefs, #list of ids
            actor = request.user.id, # id
            message = message,event = 'C',object = 'E',
            trigger_time = trigger_time
        )
    
class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.select_related('uploader').select_related('con').select_related('exer').select_related('access').all()
    serializer_class = FileSerializer
    filterset_class = FileFilter
    ordering_fields = ["id","last_update",]
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
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('file').select_related('commenter').select_related('dealer').all()
    serializer_class = CommentSerializer
    filterset_class = CommentFilter
    ordering_fields = ["id",]
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

#rights
class MailBellViewSet(viewsets.ModelViewSet):
    queryset = MailBell.objects.all()
    serializer_class = MailBellSerializer
    permission_classes = [IS]
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating mail bell via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting mail bell via API is not allowed."})
    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user=user)

class ShareViewSet(viewsets.ModelViewSet):
    queryset = Share.objects.select_related('from_user').select_related('to_user').select_related('file').all()
    serializer_class = ShareSerializer
    filterset_class = ShareFilter
    def destroy(self, request, *args, **kwargs):
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
    def sender(self,request,response,trigger_time,staff_old):# share a file
        if response.status_code == 201:
            instance = self.get_object()
            to_user = instance.to_user
            con = instance.con
            message_chief = f"{request.user.username} has shared the file {instance.file.name} in the Exercise {instance.exer.name} to {to_user.username} of Organization {to_user.org.name}."
            message_to = f"{request.user.username} has shared the file {instance.file.name} in the Exercise {instance.exer.name} to you."
            chief = OrgConRight.objects.select_related('chief').get(con=con,org=instance.user.org).chief
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
    serializer_class = FileAccessSerializer
    permission_classes = [permissions.IsAdminUser]
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating access to file via API is not allowed."})
    def update(self, request, *args, **kwargs):
        return Response({"detail":"Updating access to file via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting access to file via API is not allowed."})
    
class OrgConRightViewSet(viewsets.ModelViewSet):
    queryset = OrgConRight.objects.select_related('org').select_related('con').prefetch_related('staff').all()
    serializer_class = OrgConRightSerializer
    filterset_class = OrgConFilter
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating the right via API is not allowed."})
    def update(self, request, *args, **kwargs):# change staff
        staff_old = list(self.get_object().staff.all())
        response = super().update(request, *args, **kwargs)
        trigger_time=now()
        print("update")
        self.sender(request,response,trigger_time,staff_old)
        return response
    def destroy(self, request, *args, **kwargs):
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
    serializer_class = OrgExerRightSerializer
    filterset_class = OrgExerFilter
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating the right via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting the right via API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update','list']:
            permission_classes = [IC]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [per() for per in permission_classes]
class UserExerRightViewSet(viewsets.ModelViewSet):
    queryset = UserExerRight.objects.select_related('user').select_related('exer').all()
    serializer_class = UserExerRightSerializer
    filterset_class = UserExerFilter
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating the right via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
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
            return self.queryset.filter(user__con_staff__staff=user)

# Certain getters, perhaps abandonned
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

# Certain evaluaters
class SetUserStateView(views.APIView):
    permission_classes = [permissions.IsAdminUser]
    def get_object(self,pk):
        try:
            return CustomUser.objects.get(id=pk)
        except CustomUser.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None):
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
    def patch(self,request,pk,format=None):
        obj = self.get_object(pk)
        self.check_object_permissions(request,obj)
        serializer = SetFileStateSerializer(instance=obj,data=request.data,partial=True,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
class DistributeAccountView(views.APIView):
    permission_classes = [IPAC]
    def get_object(self,pk):
        try:
            return Contract.objects.get(id=pk)
        except Contract.DoesNotExist:
            raise Http404
    def patch(self,request,pk,format=None):
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
            return Response({'error':'You\'re not in this organization.'},status=status.HTTP_403_FORBIDDEN)
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
                chiefrightcopy(user,exer)
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
            serializer = InvitationSerializer(instance=None,data=request.data,context={"request":request}) # generate an invitation
            if serializer.is_valid():
                serializer.save()
                right = OrgConRight.objects.get(con=obj,org=org) 
                serializer.instance.send(right) # send email
                serializer.instance.token = serializer.instance.token + str(right.id) # enhence the quality of token
                serializer.instance.save()
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response("Invitation emails have been sent.",status=status.HTTP_200_OK)