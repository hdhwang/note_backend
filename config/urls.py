from django.urls import path, include, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenVerifyView
from .tokens import CustomTokenObtainPairView, CustomTokenRefreshView, CustomTokenVerifyView


schema_view = get_schema_view(
    openapi.Info(
        title="Note API",
        default_version="v1",
        description="Note API 문서",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('api/', include('api.urls')),
    path('token', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify', CustomTokenVerifyView.as_view(), name='token_verify'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# DEBUG 모드인 경우에만 추가할 URL
if settings.DEBUG == True:
    urlpatterns.append(path('admin/', admin.site.urls))
    urlpatterns.append(re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name="schema-json"))
    urlpatterns.append(re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'))
    urlpatterns.append(re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'))