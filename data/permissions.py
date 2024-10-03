# permissions of APIs
from rest_framework import permissions

from .models import CustomUser,Organization,Contract,Exercise,File,Comment
from .models import FileAccess,MailBell,Share
from .models import OrgConRight,OrgExerRight,UserExerRight


class IsPrincipalAndChief(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        obj_type_name = type(obj).__name__
        if obj_type_name == "Contract":
            chief = OrgConRight.objects.select_related('chief').get(con=obj,is_principal=True).chief
        return request.user == chief

def get_chief(obj): # generally find the chief of the obj
    obj_type_name = type(obj).__name__
    chief = None
    right = OrgConRight.objects.select_related('chief').all()
    if obj_type_name == "Exercise":#find the creator of exer
        chief = obj.chief
    if obj_type_name == "OrgConRight":
        chief = obj.chief
    if obj_type_name == "OrgExerRight":#find the creator of exer
        chief = obj.exer.chief
    if obj_type_name == "UserExerRight":#set right, find user's chief
        chief = right.filter(staff=obj.user,con=obj.exer.con).chief
    if obj_type_name == "Comment":#to assign a comment, find uploader's chief
        chief = right.filter(staff=obj.file.uploader,con=obj.file.con).chief
    if obj_type_name == "File":#to set file state, find the creator of exer
        chief = obj.exer.chief
    return chief

class IsChief(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return get_chief(obj) == request.user
    def has_permission(self, request, view):
        if request.method == "POST": # when create Exercise
            org = request.user.org
            con = request.data.get('con')
            right = OrgConRight.objects.select_related('chief').filter(con=con,org=org)
            if not right.exists():
                return False
            return right.first().chief == request.user
        return super().has_permission(request, view)

class IsSelf(permissions.BasePermission): # generally find the user of the obj
    def has_object_permission(self, request, view, obj):
        obj_type_name = type(obj).__name__
        if obj_type_name == "CustomUser":
            user = obj
        if obj_type_name == "MailBell":
            user = obj.user
        if obj_type_name == "Share":
            user = obj.from_user
        if obj_type_name == "Comment":
            user = obj.commenter
        return request.user == user
    def has_permission(self, request, view):
        if view.action == 'create': # when upload file
            exer = request.data.get('exer',None)
            if not exer:
                return False
            right = UserExerRight.objects.filter(user=request.user,exer=exer)
            return right.exists()
        return super().has_permission(request, view)
    
class CanDo(permissions.BasePermission):#Examine the rights
    def has_object_permission(self, request, view, obj):
        obj_type_name = type(obj).__name__
        if obj_type_name == 'File': # when edit a file
            access = FileAccess.objects.prefetch_related('user').get(file=obj) # can access
            if not (request.user in access.user.all()):
                return False
            right = UserExerRight.objects.filter(user=request.user,exer=obj.exer) # in the exercise
            if not right.exists:
                return False
            return right.first().rewrite
        return True
    def has_permission(self, request, view):
        if request.method == 'POST': # while creating ...
            file = request.data.get("file",None)
            if not file:
                return False
            access = FileAccess.objects.prefetch_related('user').get(file=file)
            if not (request.user in access.user.all()): # check access
                return False
            right = UserExerRight.objects.filter(user=request.user,exer=access.file.exer)
            if not right.exists: # check in the exer
                return False
            if view.queryset.model == Share: # ... a share
                return right.first().share
            if view.queryset.model == Comment: # ... a comment
                return right.first().comment
        return super().has_permission(request, view)

# class CanInvite(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return super().has_permission(request, view)

class IsOtherChief(permissions.BasePermission): # check whether a user is a chief not in charge
    def has_object_permission(self, request, view, obj):
        obj_type_name = type(obj).__name__
        if obj_type_name == 'File': # to raise boycott
            right = OrgConRight.objects.filter(con=obj.con,chief=request.user) # get chiefs
            if not right.exists(): # refuse non-chief
                return False
            if request.user.org == obj.exer.org: # refuse the chief in charge
                return False
        return super().has_object_permission(request, view, obj)