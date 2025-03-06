import logging

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.response import Response

from utils.format_helper import to_str
from api.permissions import PermissionUser
from api.serializers import UserSerializer

logger = logging.getLogger(__name__)


class AccountUserAPI(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [PermissionUser]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["put"]

    def update(self, request, *args, **kwargs):
        try:
            password = request.data.get('password')
            new_password = request.data.get('new_password')

            user_data = {
                'password': password,
                'new_password': new_password,
            }
            serializer = UserSerializer(request.user, data=user_data)
            if serializer.is_valid(raise_exception=True):
                if User.objects.values().filter(id=request.user.id) and check_password(password, User.objects.get(id=request.user.id).password):
                    user = User.objects.filter(id=request.user.id).get()
                    user.set_password(new_password)
                    user.save()
                    return Response(status=status.HTTP_200_OK)
                return Response(status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.warning(f"[AccountUserAPI - update] {to_str(e)}")
            raise
