from rest_framework import permissions
from apps.base.literals import ROUTE_GENERATION_FORBIDDEN


class IsStaffOrSuperUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser


class IsOwnerOrStaffOrSuperUser(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.is_superuser or user.role_type == 'owner'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.is_superuser or obj.id == user.id


class IsOwnerUser(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role_type == 'owner')

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and user.role_type == 'owner')


class IsRouteCompanyGenerator(permissions.BasePermission):
    message = ROUTE_GENERATION_FORBIDDEN

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        return user.role_type in ['owner', 'worker'] and hasattr(user, 'worker_profile')

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True

        if user.role_type not in ['owner', 'worker']:
            return False
        if not hasattr(user, 'worker_profile'):
            return False

        user_company_id = user.worker_profile.company_id

        if hasattr(obj, 'company_id'):
            return obj.company_id == user_company_id

        if hasattr(obj, 'route') and obj.route:
            return obj.route.company_id == user_company_id

        return False
