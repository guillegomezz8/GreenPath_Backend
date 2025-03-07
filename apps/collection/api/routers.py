from rest_framework.routers import DefaultRouter
from apps.collection.api.viewsets.collection_viewset import CollectionViewSet


router = DefaultRouter()
router.register('', CollectionViewSet, basename="collections")
urlpatterns = router.urls