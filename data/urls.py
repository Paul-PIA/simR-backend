from django.urls import path,include
from django.shortcuts import render
from . import views
from .routers import router

app_name = "data"

urlpatterns = [
    path("", views.index, name="index"),
    path('set-csrf-token/', views.set_csrf_token, name='set-csrf-token'),
    # path("<int:id>/", views.profile, name="profile"),
    path('api/', include(router.urls)),
    
    #special APIs
    path('api/adam/',views.AdamView.as_view()), # LOCK it on application

    path('api/setuserstate/<int:pk>/',views.SetUserStateView.as_view()),
    path('api/setfilestate/<int:pk>/',views.SetFileStateView.as_view()),
    path('api/assigncomment/<int:pk>/',views.AssignCommentView.as_view()),
    path('api/treatcomment/<int:pk>/',views.TreatCommentView.as_view()),
    path('api/distributeaccount/<int:pk>/',views.DistributeAccountView.as_view()),
    path('api/setchief/<int:pk>/',views.SetChiefView.as_view()),
    path('api/forgotpassword/',views.ForgotPasswordView.as_view()),

    path('api/raiseboycott/<int:pk>/',views.RaiseBoycottView.as_view()),

    path('api/invitechief/<int:pk>/',views.InviteChiefView.as_view()),
    path('api/resetpasswordconfirm/<str:uid>/<str:token>/',views.ResetPasswordConfirmView.as_view()),
    path('api/fusecomments/',views.FuseCommentsView.as_view()),
    path('api/sidebar/',views.SidebarView.as_view()),
    path('api/homedata/',views.HomeView.as_view())
    #path('api/test/',views.TestView.as_view()),


]
