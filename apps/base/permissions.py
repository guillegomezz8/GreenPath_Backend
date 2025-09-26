from rest_framework import permissions

class IsStaffOrSuperUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser

class IsOwnerOrStaffOrSuperUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.is_superuser or obj.id == request.user.id
    
class IsOwnerUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user.role_type == 'owner'
