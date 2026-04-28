import ipaddress
import logging

from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


from utils.format_helper import to_int
from utils.regex_helper import ip_cidr_regex
from api.models import ChoiceResult, choice_str_to_int, AuditLog
from api.permissions import PermissionAdmin
from api.serializers import AuditLogSerializer
from utils.export_helper import export_to_zip


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

    # 정렬 적용 필드 : (실제 필드, 파라미터 명)으로 기재
    ordering = filters.OrderingFilter(
        fields = (
            ('id', 'id'),
            ('user', 'user'),
            ('ip', 'ip'),
            ('category', 'category'),
            ('sub_category', 'sub_category'),
            ('action', 'action'),
            ('result', 'result'),
            ('date', 'date')
        )
    )

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
    permission_classes = [PermissionAdmin]

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

    # )

    @action(detail=False, methods=['get'])
    def export(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        field_mappings = {
            'user': '사용자',
            'ip': 'IP 주소',
            'category': '카테고리',
            'sub_category': '세부 카테고리',
            'action': '수행 작업',
            'result': '결과',
            'date': '일시',
        }
        
        data_list = []
        for obj in queryset:
            data_list.append({
                'user': obj.user,
                'ip': str(ipaddress.IPv4Address(obj.ip)) if obj.ip else '',
                'category': obj.category,
                'sub_category': obj.sub_category,
                'action': obj.action,
                'result': obj.get_result_display(),
                'date': obj.date,
            })
            
        return export_to_zip(data_list, field_mappings, "감사 로그")