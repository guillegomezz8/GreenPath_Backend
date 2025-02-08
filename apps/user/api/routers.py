from rest_framework.routers import DefaultRouter

from apps.user.api.viewsets.user_viewset import UserViewSet


router = DefaultRouter()
router.register('', UserViewSet, basename="users")
urlpatterns = router.urls