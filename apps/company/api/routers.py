from rest_framework.routers import DefaultRouter
from apps.company.api.viewsets.company_viewset import CompanyViewSet


router = DefaultRouter()
router.register('', CompanyViewSet, basename="companies")
urlpatterns = router.urls