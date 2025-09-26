from rest_framework.routers import DefaultRouter
from apps.truck.api.viewsets.truck_viewset import TruckViewSet


router = DefaultRouter()
router.register('', TruckViewSet, basename="trucks")
urlpatterns = router.urls