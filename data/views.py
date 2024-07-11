# from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,Http404
from rest_framework import viewsets,views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import CustomUser,Organization,Contract,Exercise,File,Comment
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserExerRight

from .serializers import UserSerializer,OrgSerializer,ConSerializer,ExerSerializer,FileSerializer,CommentSerializer,ShareSerializer
from .serializers import MailBellSerializer,FileAccessSerializer
from .serializers import OrgConRightSerializer,OrgExerRightSerializer,UserExerRightSerializer
from .serializers import SpaceShareSerializer,SpaceSerializer

from .filters import UserFilter,OrgFilter,ConFilter,ExerFilter,FileFilter,CommentFilter
from .filters import OrgConFilter,OrgExerFilter,UserExerFilter

from .permissions import IsAdmin as IA,IsPrincipalAndChief as IPAC,IsChief as IC,IsSelf as IS,IsInvited as II
from .permissions import CanDo as CD
# from django.template import loader
# from .serializers import TestSerializer

from django.shortcuts import HttpResponse
from django.contrib.auth import get_user_model

def create_superuser_view(request):
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        return HttpResponse("Superuser created successfully.")
    return HttpResponse("Superuser already exists.")


def index(request):
    return HttpResponse("Here drops the principal homepage.")

# def profile(request,id):
#     name = CustomUser.__str__(CustomUser.getter(id))
#     return HttpResponse("Here drops the homepage of %s." % name)

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IS,]
    filterset_class = UserFilter
    ordering_fields = ["id",]
    def create(self,request,*args,**kwargs): 
        return Response({"detail":"Creating users via this API is not allowed."})
class OrgViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrgSerializer
    permission_classes = [IA]
    filterset_class = OrgFilter
    ordering_fields = ["id",]
class ConViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ConSerializer
    permission_classes = [IA,II,IPAC]
    filterset_class = ConFilter
    ordering_fields = ["id",]
class ExerViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerSerializer
    permission_classes = [IA,IC]
    filterset_class = ExerFilter
    ordering_fields = ["id","date_i","date_f"]

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IA,]
    filterset_class = FileFilter
    ordering_fields = ["id","last_update",]
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IA,IS,CD]
    filterset_class = CommentFilter
    ordering_fields = ["id",]

class MailBellViewSet(viewsets.ModelViewSet):
    queryset = MailBell.objects.all()
    serializer_class = MailBellSerializer
    permission_classes = [IS]
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating mail bell via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting mail bell via API is not allowed."})

class ShareViewSet(viewsets.ModelViewSet):
    queryset = Share.objects.all()
    serializer_class = ShareSerializer
    permission_classes = [IS,CD]
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting share record via API is not allowed."})

class FileAccessViewSet(viewsets.ModelViewSet):
    queryset = FileAccess.objects.all()
    serializer_class = FileAccessSerializer
    permission_classes = [IA,]
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating access to file via API is not allowed."})
    def update(self, request, *args, **kwargs):
        return Response({"detail":"Updating access to file via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting access to file via API is not allowed."})

class OrgConRightViewSet(viewsets.ModelViewSet):
    queryset = OrgConRight.objects.all()
    serializer_class = OrgConRightSerializer
    permission_classes = [IC,II]
    filterset_class = OrgConFilter
    # def get_queryset(self):
    #     queryset= super().get_queryset()
    #     org = self.request.query_params.get("org")
    #     con = self.request.query_params.get("con")
    #     if org and con:
    #         queryset =  queryset.filter(org=org,con=con)
    #     elif org or con:
    #         return Response({"message":"org and con parameters are both required"})
    #     return queryset
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating the right via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting the right via API is not allowed."})
class OrgExerRightViewSet(viewsets.ModelViewSet):
    queryset = OrgExerRight.objects.all()
    serializer_class = OrgExerRightSerializer
    permission_classes = [IPAC]
    filterset_class = OrgExerFilter
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating the right via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting the right via API is not allowed."})
class UserExerRightViewSet(viewsets.ModelViewSet):
    queryset = UserExerRight.objects.all()
    serializer_class = UserExerRightSerializer
    permission_classes = [IC]
    filterset_class = UserExerFilter
    def create(self, request, *args, **kwargs):
        return Response({"detail":"Creating the right via API is not allowed."})
    def destroy(self, request, *args, **kwargs):
        return Response({"detail":"Deleting the right via API is not allowed."})


# class UserConRightViewSet(viewsets.ModelViewSet): #### will be abandonned
#     queryset = UserConRight.objects.all()
#     serializer_class = UserConRightSerializer
#     permission_classes = [AllowAny]
#     filterset_class = UserConFilter
#     def create(self, request, *args, **kwargs):
#         return Response({"detail":"Creating the right via API is not allowed."})
#     def destroy(self, request, *args, **kwargs):
#         return Response({"detail":"Deleting the right via API is not allowed."})

# Spaces
class MySpaceShareView(views.APIView):
    permission_classes = [AllowAny]
    def get(self,request,*args,**kwargs):
        exer = request.query_params.get('exer')
        to_user = request.query_params.get('to_user')
        from_user = request.query_params.get('from_user')
        if exer:
            if to_user and from_user:
                return Response({"message":"Only one parameter is permitted."})
            elif not (to_user or from_user):
                return Response({"message":"Parameter to_user XOR from_user is required."})
            else:
                if to_user:
                    share = Share.objects.filter(to_user=to_user,file__exer=exer)
                else:
                    share = Share.objects.filter(from_user=from_user,file__exer=exer)
                serializer = SpaceShareSerializer(share,many=True)
            return Response(serializer.data)
        else:
            return Response({"message":"Parameter exer is required."})
class MySpaceAllView(views.APIView):
    permission_classes = [AllowAny]
    def get(self,request,*args,**kwargs):
        exer = request.query_params.get('exer')
        user = request.query_params.get('user')
        if user and exer:
            file = FileAccess.objects.filter(user=user,file__exer=exer)
            serializer = SpaceSerializer(file,many=True)
            return Response(serializer.data)
        elif user:
            return Response({"message":"Parameter exer is required."})
        elif exer:
            return Response({"message":"Parameter user is required."})
        else:
            return Response({"message":"Parameters exer, user are required."})

class OrgSpaceView(views.APIView):
    permission_classes = [AllowAny]
    def get(self,request,*args,**kwargs):
        exer = request.query_params.get('exer')
        is_template = request.query_params.get('is_template')
        org = request.user.org
        if exer:
            if is_template:
                file = FileAccess.objects.filter(file__is_template=True,org=org)
            else:
                file = FileAccess.objects.filter(org=org)
            serializer = SpaceSerializer(file,many=True)
            return Response(serializer.data)
        else:
            return Response({"message":"Parameter exer is required."})
class PublicSpaceView(views.APIView):
    permission_classes = [AllowAny]
    def get(self,request,*args,**kwargs):
        exer = request.query_params.get('exer')
        org = request.query_params.get('org')
        is_template = request.query_params.get('is_template')
        if not exer:
            return Response({"message":"Parameter exer is required."})
        elif is_template and org:
            return Response({"message":"Parameter is_template XOR org is required."})
        elif is_template:
            file = FileAccess.objects.filter(file__is_template=True,file__exer=exer)
        elif org:
            file = FileAccess.objects.filter(file__is_public=True,file__exer=exer,org=org)
        else:
            return Response({"message":"Parameter is_template XOR org is required."})
        serializer = SpaceSerializer(file,many=True)
        return Response(serializer.data)


# class TestViewSet(viewsets.ModelViewSet):
#     queryset = Contract.objects.all()
#     serializer = TestSerializer
#     permission_classes = [AllowAny]
#     def create(self, request, *args, **kwargs):
#         return super().create(request, *args, **kwargs)