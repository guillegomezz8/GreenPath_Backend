from rest_framework import permissions

class IsOwnerOrStaffOrSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or staff or superusers to edit it.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.is_superuser or obj.id == request.user.id
    
class IsOwnerUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user.role == 'owner'
