# permissions.py

from rest_framework.permissions import BasePermission


class IsAdminOrSuperAdmin(BasePermission):

    message = "You do not have permission to add students."

    def has_permission(self, request, view):

        # User must be logged in
        if not request.user or not request.user.is_authenticated:
            return False

        # Only SuperAdmin or Admin can add students
        return request.user.role in ['SuperAdmin', 'Admin']