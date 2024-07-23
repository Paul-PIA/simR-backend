# from django.shortcuts import render,get_object_or_404
from django.db import models
from django.http import HttpResponse,Http404
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
# from .serializers import TestSerializer


def index(request):
    return HttpResponse("Here drops the principal homepage.")

# def profile(request,id):
#     name = CustomUser.__str__(CustomUser.getter(id))
#     return HttpResponse("Here drops the homepage of %s." % name)

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
    def get_permissions(self):
        if self.action in ['create','update','partial_update','destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [per() for per in permission_classes]
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
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting the right via API is not allowed."})
    def get_permissions(self):
        if self.action in ['update','partial_update']:
            permission_classes = [IPAC]
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
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
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
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
class SetChiefView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self,pk):
        try:
            return OrgConRight.objects.get(id=pk)
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
            exers = obj.con.exers.all()
            for exer in exers:
                UserExerRight.objects.create(user=user,exer=exer)
                chiefrightcopy(user,exer)
            invitation.is_used = True
            invitation.save()
            return Response({'message':'You have participate in the contract.'},status=status.HTTP_200_OK)
        except Invitation.DoesNotExist: 
            return Response({'error':'Invalid invitation token.'},status=status.HTTP_404_NOT_FOUND)

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
                serializer.instance.send(right.id) # send email
                serializer.instance.token = serializer.instance.token + str(right.id) # enhence the quality of token
                serializer.instance.save()
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response("Invitation emails have been sent.",status=status.HTTP_200_OK)

# class TestViewSet(viewsets.ModelViewSet):
#     queryset = Contract.objects.all()
#     serializer = TestSerializer
#     permission_classes = [AllowAny]
#     def create(self, request, *args, **kwargs):
#         return super().create(request, *args, **kwargs)