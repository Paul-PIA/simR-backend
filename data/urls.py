<<<<<<< HEAD
from django.urls import path
from django.shortcuts import render
from .views import get_user_emails
from . import views
=======
from django.urls import path,include
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView


from . import views
from .routers import router
>>>>>>> master

app_name = "data"

urlpatterns = [
    path("", views.index, name="index"),
<<<<<<< HEAD
    path("<int:id>/", views.profile, name="profile"),
    path('user-emails/', get_user_emails, name='get_user_emails'),
    #path("<int:id>/project/", views.proj, name="proj"),
    #path("<int:id>/exercise/", views.exer, name="exer"),
    #path("<int:id>/organization/", views.org, name="org"),
    
    #path("<int:id>/settings/", views.settings, name="settings"),
    #path("<int:id>/chats/", views.chats, name="chats"),
    #path("<int:id>/help/", views.help, name="help"),


]

=======
    # path("<int:id>/", views.profile, name="profile"),
    path('api/', include(router.urls)),
    #registration
    path('api/auth/',include('dj_rest_auth.urls')),
    path('api/auth/registration/',include('dj_rest_auth.registration.urls')),
    path('api/auth/social/',include('allauth.socialaccount.urls')),
    #password reset, not passed test 
    path('api/auth/password/reset/',PasswordResetView.as_view(),name='rest_password_reset_override'),
    path('api/auth/password/reset/confirm/<uidb64>/<token>/',PasswordResetConfirmView.as_view(),name='password_reset_confirm_override'),
    #to get token for API requests
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    #special APIs
    path('api/setuserstate/',views.SetUserStateView.as_view()),
    path('api/setfilestate/',views.SetFileStateView.as_view()),
    path('api/assigncomment/',views.AssignCommentView.as_view()),
    path('api/treatcomment/',views.TreatCommentView.as_view()),
    path('api/distributeaccount/',views.DistributeAccountView.as_view()),
    path('api/setchief/',views.SetChiefView.as_view()),
    path('api/raiseboycott/',views.RaiseBoycottView.as_view()),

    path('api/invitechief/',views.InviteChiefView.as_view()),
    #path('api/test/',views.TestView.as_view()),
]
>>>>>>> master
