# register Viewset Objects to the url
from rest_framework import routers
from django.urls import path,include

from data.views import UserViewSet,OrgViewSet,ConViewSet,ExerViewSet,FileViewSet,CommentViewSet,ShareViewSet
from data.views import FileAccessViewSet,MailBellViewSet
from data.views import OrgConRightViewSet,OrgExerRightViewSet,UserExerRightViewSet
router = routers.SimpleRouter()

router.register(r'user', UserViewSet)
router.register(r'organization', OrgViewSet)
router.register(r'contract', ConViewSet)
router.register(r'exercise', ExerViewSet)
router.register(r'file', FileViewSet)
router.register(r'comment', CommentViewSet)
router.register(r'share', ShareViewSet)

router.register(r'mailbell', MailBellViewSet)
router.register(r'access', FileAccessViewSet)
router.register(r'orgconright', OrgConRightViewSet)
router.register(r'orgexerright', OrgExerRightViewSet)
router.register(r'userexerright', UserExerRightViewSet)

urlpatterns = router.urls