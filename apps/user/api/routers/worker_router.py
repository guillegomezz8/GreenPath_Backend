from rest_framework.routers import DefaultRouter

from apps.user.api.viewsets.worker_viewset import WorkerViewSet


router = DefaultRouter()
router.register('', WorkerViewSet, basename="workers")
urlpatterns = router.urls