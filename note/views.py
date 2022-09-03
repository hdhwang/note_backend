from rest_framework import viewsets, versioning

from .models import AuditLog                # 모델 불러오기
from .serializers import AuditLogSerializer # 시리얼라이저 불러오기
from django_filters import rest_framework as filters


class CustomURLPathVersioning(versioning.URLPathVersioning):
    allowed_versions = ['v1']


class AuditLogFilter(filters.FilterSet):
    class Meta:
        model = AuditLog

class AuditLogViewSet(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ['get']
    # http_method_names = ['get', 'post', 'put', 'delete']

    # 커스텀 필터 클래스 적용
    filterset_class = AuditLogFilter

    # 정렬 적용 필드
    ordering_fields = ['id']