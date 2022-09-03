from rest_framework import viewsets, versioning
from .models import AuditLog
from .serializers import AuditLogSerializer
from django_filters import rest_framework as filters


class CustomURLPathVersioning(versioning.URLPathVersioning):
    allowed_versions = ['v1']


class AuditLogFilter(filters.FilterSet):
    user = filters.CharFilter(lookup_expr='icontains')

    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = ('id', 'ip', 'category', 'sub_category', 'action', 'result')


class AuditLogAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ['get']
    # http_method_names = ['get', 'post', 'put', 'delete']

    # 커스텀 필터 클래스 적용
    filterset_class = AuditLogFilter

    # 필터 적용 필드 (커스텀 필터 클래스를 적용하지 않는 경우 사용)
    # filterset_fields = ('id', 'user', 'ip', 'category', 'sub_category', 'action', 'result', 'date')

    # 필터 적용 필드 (like 검색, 범위 검색 등을 적용할 때)
    # filterset_fields = {
    #     'id': ['exact'],
    #     'user': ['exact', 'icontains'],
    #     'ip': ['exact', 'icontains'],
    #     'category': ['exact'],
    #     'sub_category': ['exact'],
    #     'action': ['icontains'],
    #     'result': ['exact'],
    #     'date': ['exact', 'gte', 'lte'],
    # }

    # 정렬 적용 필드
    ordering_fields = ['id', 'user', 'ip', 'category', 'sub_category', 'action', 'result', 'date']