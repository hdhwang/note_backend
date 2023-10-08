from datetime import datetime
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        result = super().validate(attrs)

        refresh = self.get_token(self.user)

        result['refresh'] = str(refresh)
        result['refresh_exp'] = str(datetime.now() + refresh.lifetime)
        result['access'] = str(refresh.access_token)
        result['access_exp'] = str(datetime.now() + refresh.access_token.lifetime)

        return result


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer