from django.contrib import admin

# Register your models here.
from .models import CustomUser,Organization,Contract,Exercise,File,Comment
from .models import OrgConRights,OrgExerRights,UserConRights,UserExerRights,MailBell,FileAccess

### instances
@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','first_name','last_name','username','email','last_login')
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

### rights
