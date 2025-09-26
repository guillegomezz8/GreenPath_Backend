from rest_framework.routers import DefaultRouter

from apps.user.api.viewsets.client_viewset import ClientViewSet


router = DefaultRouter()
router.register('', ClientViewSet, basename="clients")
urlpatterns = router.urls