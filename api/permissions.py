from rest_framework import permissions


def check_admin(request):
    return request.user.groups.filter(name="관리자").exists()

def check_user(request):
    return request.user.groups.filter(name="사용자").exists()


class PermissionAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return check_admin(request) or check_user(request)

        return check_admin(request)


class PermissionUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return check_admin(request) or check_user(request)
