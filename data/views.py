from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,Http404
from django.template import loader
from django.http import JsonResponse
from .models import CustomUser

def index(request):
    return HttpResponse("Here drops the principal homepage.")

def profile(request,id):
    name = CustomUser.__str__(CustomUser.get_user(id))
    return HttpResponse("Here drops the homepage of %s." % name)


def get_user_emails(request):
    emails = CustomUser.objects.values_list('email', flat=True)
    return JsonResponse(list(emails), safe=False)


from django.contrib.auth.models import User

def create_superuser(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
        return HttpResponse('Superuser created successfully')
    return HttpResponse('Superuser already exists')

