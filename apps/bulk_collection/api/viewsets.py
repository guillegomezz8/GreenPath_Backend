from django.db.models import Q
from django_filters.rest_framework import BooleanFilter, CharFilter, DateFilter, DjangoFilterBackend, FilterSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.viewsets import ModelViewSet

from apps.base.permissions import IsOwnerUser
from apps.company.utils import resolve_user_company
from apps.company.permissions import IsBulkCollectionsEnabled
from apps.bulk_collection.api.serializers import BulkCollectionSerializer
from apps.bulk_collection.models import BulkCollection


class BulkCollectionFilter(FilterSet):
    start_date = DateFilter(field_name="collection_date", lookup_expr="gte")
    end_date = DateFilter(field_name="collection_date", lookup_expr="lte")
    billable = BooleanFilter(field_name="billable")
    unit = CharFilter(field_name="unit", lookup_expr="exact")
    search = CharFilter(method="filter_search")

    class Meta:
        model = BulkCollection
        fields = ("client", "unit", "billable", "start_date", "end_date", "search")

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(client__name__icontains=value)
            | Q(client__cif__icontains=value)
            | Q(notes__icontains=value)
        ).distinct()


class BulkCollectionViewSet(ModelViewSet):
    serializer_class = BulkCollectionSerializer
    permission_classes = (IsAuthenticated, IsBulkCollectionsEnabled, IsOwnerUser)
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = BulkCollectionFilter

    def get_queryset(self):
        company = resolve_user_company(self.request.user)
        if not company:
            return BulkCollection.objects.none()
        return BulkCollection.objects.select_related("company", "client").filter(company=company)

    def perform_create(self, serializer):
        serializer.save(company=resolve_user_company(self.request.user))
