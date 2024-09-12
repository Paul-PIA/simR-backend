# register Viewset Objects to the url
from rest_framework import routers
from django.urls import path,include

from data.views import UserViewSet,OrgViewSet,ConViewSet,ExerViewSet,FileViewSet,CommentViewSet,ShareViewSet,NotificationViewSet
from data.views import FileAccessViewSet,MailBellViewSet
from data.views import OrgConRightViewSet,OrgExerRightViewSet,UserExerRightViewSet
router = routers.SimpleRouter()

router.register(r'user', UserViewSet,basename='User')
router.register(r'organization', OrgViewSet,basename='Organization')
router.register(r'contract', ConViewSet,basename='Contract')
router.register(r'exercise', ExerViewSet,basename='Exxercise')
router.register(r'file', FileViewSet,basename='File')
router.register(r'comment', CommentViewSet,basename='Comment')
router.register(r'share', ShareViewSet,basename='Share')
router.register(r'notification', NotificationViewSet,basename='Notification')

router.register(r'mailbell', MailBellViewSet,basename='Mailbell')
router.register(r'access', FileAccessViewSet,basename='File Access')
router.register(r'orgconright', OrgConRightViewSet,basename='OrgConRight')
router.register(r'orgexerright', OrgExerRightViewSet,basename='OrgExerRight')
router.register(r'userexerright', UserExerRightViewSet,basename='UserExerRight')

urlpatterns = router.urls
