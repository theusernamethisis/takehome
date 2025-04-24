from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from candidate_fyi_takehome_project.users.api.views import UserViewSet

from interviews.views import InterviewTemplateViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("interviews", InterviewTemplateViewSet)


app_name = "api"
urlpatterns = router.urls