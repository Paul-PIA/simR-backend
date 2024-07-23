from django.contrib import admin

# Register your models here.
from .models import CustomUser,Organization,Contract,Exercise,File,Comment
from .models import OrgConRight,OrgExerRight,UserExerRight,MailBell,FileAccess,Share

### instances
@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','first_name','last_name','username','email','last_login','org')
    list_filter = ('last_login','date_joined')

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id','name','email')
    list_filter = ()

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id','name')
    list_filter = ('org',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id','date_i','date_f','type')
    list_filter = ('date_i','date_f','type')

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id','name')
    list_filter = ('is_commented','is_boycotted','is_final')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id','file','text')
    list_filter = ('is_treated',)

### right
@admin.register(MailBell)
class MailBellAdmin(admin.ModelAdmin):
    list_display = ('user',)
    list_filter = ()
@admin.register(FileAccess)
class AccessAdmin(admin.ModelAdmin):
    list_display = ('file',)
    list_filter = ('user','org',)
@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('id','from_user','to_user','date','file','between_org',)
    list_filter = ('date','between_org',)

@admin.register(OrgConRight)
class OrgConAdmin(admin.ModelAdmin):
    list_display = ('id','org','con','chief')
    list_filter = ('org','con')
@admin.register(OrgExerRight)
class OrgExerAdmin(admin.ModelAdmin):
    list_display = ('id','org','exer')
    list_filter = ('org','exer')
@admin.register(UserExerRight)
class UserExerAdmin(admin.ModelAdmin):
    list_display = ('id','user','exer')
    list_filter = ('user','exer')
