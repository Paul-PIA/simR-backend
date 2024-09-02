from django.urls import path,include
from django.shortcuts import render
from . import views
from .routers import router

app_name = "data"

urlpatterns = [
    path("", views.index, name="index"),
    # path("<int:id>/", views.profile, name="profile"),
    path('api/', include(router.urls)),
    
    #special APIs
    path('api/adam/',views.AdamView.as_view()), # LOCK it in the real server

    path('api/setuserstate/<int:pk>/',views.SetUserStateView.as_view()),
    path('api/setfilestate/<int:pk>/',views.SetFileStateView.as_view()),
    path('api/assigncomment/<int:pk>/',views.AssignCommentView.as_view()),
    path('api/treatcomment/<int:pk>/',views.TreatCommentView.as_view()),
    path('api/distributeaccount/<int:pk>/',views.DistributeAccountView.as_view()),
    path('api/setchief/<int:pk>/',views.SetChiefView.as_view()),
    path('api/raiseboycott/<int:pk>/',views.RaiseBoycottView.as_view()),

    path('api/invitechief/<int:pk>/',views.InviteChiefView.as_view()),
    #path('api/test/',views.TestView.as_view()),


]
