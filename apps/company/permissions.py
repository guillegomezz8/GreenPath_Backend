from rest_framework.permissions import BasePermission

from apps.company.utils import get_user_company_features
from apps.base.literals import COMPANY_FEATURE_DISABLED


class IsCompanyFeatureEnabled(BasePermission):
    feature_name = None
    message = COMPANY_FEATURE_DISABLED

    def has_permission(self, request, view):
        if not self.feature_name:
            return True
        return bool(get_user_company_features(request.user).get(self.feature_name, False))


class IsCollectionsEnabled(IsCompanyFeatureEnabled):
    feature_name = "collections_enabled"


class IsBulkCollectionsEnabled(IsCompanyFeatureEnabled):
    feature_name = "bulk_collections_enabled"
