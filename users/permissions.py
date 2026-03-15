from rest_framework import permissions

from users.enums import UserTypeChoices

class IsAdmin(permissions.BasePermission):
    """
    Only allow access to authenticated users of type ADMIN
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_active
            and request.user.is_authenticated
            and request.user.type == UserTypeChoices.ADMIN
        )

class IsDriver(permissions.BasePermission):
    """
    Allows access only to authenticated users with type DRIVER.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.type == UserTypeChoices.DRIVER
        )


class IsGuardian(permissions.BasePermission):
    """
    Allows access only to authenticated users with type GUARDIAN.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.type == UserTypeChoices.GUARDIAN
        )
