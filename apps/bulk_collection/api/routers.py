from rest_framework.routers import DefaultRouter

from apps.bulk_collection.api.viewsets import BulkCollectionViewSet


router = DefaultRouter()
router.register("", BulkCollectionViewSet, basename="bulk-collections")
urlpatterns = router.urls
