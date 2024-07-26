from django.urls import path,include
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView
from . import views
from .routers import router

app_name = "data"

urlpatterns = [
    path("", views.index, name="index"),
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
