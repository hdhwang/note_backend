import ipaddress
import logging

from django_filters import rest_framework as filters
from rest_framework import viewsets

from utils.format_helper import to_int
from utils.regex_helper import ip_cidr_regex
from api.models import ChoiceResult, choice_str_to_int, AuditLog
from api.permissions import PermissionSuperUser
from api.serializers import AuditLogSerializer

logger = logging.getLogger(__name__)


class AuditLogFilter(filters.FilterSet):
    result_list = [
        list(reversed(choice_result)) for choice_result in list(ChoiceResult.choices)
    ]

    user = filters.CharFilter(lookup_expr="icontains")
    ip = filters.CharFilter(method="ip_range_filter")
    result = filters.ChoiceFilter(
        choices=result_list,
        method="result_filter",
        help_text=f'Available values : {", ".join(list(zip(*ChoiceResult.choices))[1])}',
    )

    def ip_range_filter(self, queryset, name, value):
        # IP 주소 또는 CIDR 형태인 경우 (192.168.0.1 OR 192.168.0.1/24)
        if ip_cidr_regex.match(value):
            ip_addr = ipaddress.ip_network(value, False)

            start_ip = to_int(ip_addr.network_address)
            end_ip = to_int(ip_addr.broadcast_address)

            return queryset.filter(ip__gte=start_ip, ip__lte=end_ip)

        else:
            return queryset.filter(ip=value)

    def result_filter(self, queryset, name, value):
        return queryset.filter(result=choice_str_to_int(ChoiceResult, value))

    start_date = filters.DateTimeFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "user",
            "ip",
            "category",
            "sub_category",
            "action",
            "result",
            "start_date",
            "end_date",
        )


class AuditLogAPI(viewsets.ModelViewSet):
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    permission_classes = [PermissionSuperUser]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get"]

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
    ordering_fields = [
        "id",
        "user",
        "ip",
        "category",
        "sub_category",
        "action",
        "result",
        "date",
    ]