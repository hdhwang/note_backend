from datetime import datetime, timedelta
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer, TokenVerifySerializer
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.tokens import UntypedToken
from utils.formatHelper import *
from utils.logHelper import insert_audit_log


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        action = f"아이디 또는 비밀번호 불일치 (아이디 : {attrs.get('username')})"
        user = None
        result = False
        try:
            data = super().validate(attrs)
            user = attrs.get('username')
            action = "사용자 로그인"
            result = True

            refresh = self.get_token(self.user)
            data['refresh_exp'] = str(datetime.now() + refresh.lifetime)
            data['access_exp'] = str(datetime.now() + refresh.access_token.lifetime)

            return data
        finally:
            insert_audit_log(user, self.context.get('request'), "계정", "로그인", action, result)

    def get_token(cls, user):
        token = super().get_token(user)
        token['first_name'] = user.first_name
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser
        token['groups'] = list(user.groups.values_list('name',flat = True))
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.token_class(attrs["refresh"])
        data['access_exp'] = str(datetime.now() + refresh.access_token.lifetime)

        return data


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class CustomTokenVerifySerializer(TokenVerifySerializer):
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        token = UntypedToken(attrs["token"])
        data['user'] = {
            'id': token.get('username'),
            'name': token.get('first_name'),
            'email': token.get('email'),
            'is_superuser': token.get('is_superuser'),
            'groups': token.get('groups'),
        }
        return data


class CustomTokenVerifyView(TokenVerifyView):
    serializer_class = CustomTokenVerifySerializer