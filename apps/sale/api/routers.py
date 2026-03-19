from rest_framework.routers import DefaultRouter

from apps.sale.api.viewsets.buyer_viewset import BuyerViewSet
from apps.sale.api.viewsets.sale_viewset import SaleViewSet


router = DefaultRouter()
router.register("buyers", BuyerViewSet, basename="buyers")
router.register("sales", SaleViewSet, basename="sales")
urlpatterns = router.urls
