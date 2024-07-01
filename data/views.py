from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,Http404
from django.template import loader
from django.http import JsonResponse
from .models import CustomUser
from asgiref.sync import sync_to_async

# Vue asynchrone pour la page d'accueil
async def index(request):
    return HttpResponse("Here drops the principal homepage.")

# Vue asynchrone pour le profil utilisateur
async def profile(request, id):
    user_name = await sync_to_async(lambda: str(CustomUser.get_user(id)))()
    return HttpResponse("Here drops the homepage of %s." % user_name)

# Vue asynchrone pour obtenir les emails des utilisateurs
async def get_user_emails(request):
    emails = await sync_to_async(lambda: list(CustomUser.objects.values_list('email', flat=True)))()
    return JsonResponse(emails, safe=False)
