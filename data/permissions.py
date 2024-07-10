from rest_framework import permissions

from .models import CustomUser,Organization,Contract,Exercise,File,Comment
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserExerRight

class IsAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        obj_type_name = type(obj).__name__
        if request.method in permissions.SAFE_METHODS:#stop getting some sensible data
            if request.method == 'GET':
                return request.user.is_staff 
            return True
        if obj_type_name == "Organization":#control Organization
            return request.user.is_staff
        if obj_type_name == "Contract":#delete Contract
            if request.method == 'DELETE':
                return request.user.is_staff
        # if obj_type_name == "CustomUser":
        #     if request.data.get('is_active',None):
        #         return request.user.is_staff
        #     if request.data.get('is_staff',None):
        #         return request.user.is_staff
        #     if request.data.get('is_superuser',None):
        #         return request.user.is_staff
        #     else:
        #         return True
        return True

class IsInvited(permissions.BasePermission):#A modifier
    def has_object_permission(self, request, view, obj):
        return True

class IsPrincipalAndChief(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'PUT' and request.method == 'PATCH':#update Contrat and OrgConRight
            obj_type_name = type(obj).__name__
            if obj_type_name == "Contract":
                chief = OrgConRight.objects.get(con=obj,is_principal=True).chief
            if obj_type_name == "OrgExerRight":
                chief = OrgConRight.objects.get(con=obj.con,is_principal=True).chief
            return request.user == chief
        return True

class IsChief(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:#pass get
            return True
        obj_type_name = type(obj).__name__
        if obj_type_name == "Exercise":#control Exercise
            chief = OrgConRight.objects.get(con=obj.con,org=obj.org).chief
        if request.method == 'PUT' or request.method == 'PATCH':#update OrgConRight,UserExerRight
            if obj_type_name == "OrgConRight":
                chief = obj.chief
            if obj_type_name == "UserExerRight":
                chief = OrgConRight.objects.get(con=obj.exer.con,org=obj.user.org).chief
        return chief == request.user

class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        obj_type_name = type(obj).__name__
        if request.method == 'PUT' or request.method == 'PATCH':#update User,MailBell,Share,Comment
            if obj_type_name == "CustomUser":
                user = obj
            elif obj_type_name == "MailBell":
                user = obj.user
            elif obj_type_name == "Share":
                user = obj.from_user
            elif obj_type_name == "Comment":
                user = obj.commenter
            return request.user == user
        elif request.method == 'DELETE':#delete User,Comment
            obj_type_name = type(obj).__name__
            if obj_type_name == "CustomUser":
                user = obj
            if obj_type_name == "Comment":
                user = obj.commenter
            return request.user == user
        return True
    
class CanDo(permissions.BasePermission):#Examine the right
    def has_object_permission(self, request, view, obj):
        obj_type_name = type(obj).__name__
        if request.method == 'POST': # to upload,comment and share
            data = request.query_params
            if obj_type_name == 'Comment':
                return False
                # file = data.get('file',None)
                # if not file:
                #     return False
                # access = FileAccess.objects.get(file=file)
                # if not (request.user in access.user.all()):
                #     return False
                # right = UserExerRight.objects.filter(user=request.user,exer=file.exer)
                # if not right.exists:
                #     return False
                # return right.comment
        #     if obj_type_name == 'Share':
        #         file = data.get('file',None)
        #         if not file:
        #             return False
        #         access = FileAccess.objects.get(file=file)
        #         if not (request.user in access.user.all()):
        #             return False
        #         right = UserExerRight.objects.filter(user=request.user,exer=file.exer)
        #         if not right.exists:
        #             return False
        #         return right.share
        
