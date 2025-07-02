from rest_framework.routers import DefaultRouter
from apps.zone.api.viewsets.zone_viewset import  ZoneViewSet


router = DefaultRouter()
router.register('', ZoneViewSet, basename="zones")
urlpatterns = router.urls