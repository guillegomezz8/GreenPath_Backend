from rest_framework.routers import DefaultRouter
from apps.route.api.viewsets.route_viewset import RouteViewSet


router = DefaultRouter()
router.register('', RouteViewSet, basename="routes")
urlpatterns = router.urls