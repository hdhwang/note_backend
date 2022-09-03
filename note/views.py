from rest_framework import viewsets, versioning
from .models import AuditLog, BankAccount, GuestBook, Note, Serial
from .serializers import AuditLogSerializer, BankAccountSerializer, GuestBookSerializer, NoteSerializer, SerialSerializer
from django_filters import rest_framework as filters
from utils.AESHelper import make_enc_value
from utils.formatHelper import *
from utils.regexHelper import *


class CustomURLPathVersioning(versioning.URLPathVersioning):
    allowed_versions = ['v1']


class AuditLogFilter(filters.FilterSet):
    user = filters.CharFilter(lookup_expr='icontains')
    ip = filters.CharFilter(method='ip_range_filter')

    def ip_range_filter(self, queryset, value, *args):
        input_value = args[0]

        # IP 주소 또는 CIDR 형태인 경우 (192.168.0.1 OR 192.168.0.1/24)
        if ip_cidr_regex.match(input_value):
            ip_addr = ipaddress.ip_network(input_value, False)

            start_ip = to_int(ip_addr.network_address)
            end_ip = to_int(ip_addr.broadcast_address)

            return queryset.filter(ip__gte=start_ip, ip__lte=end_ip)

        else:
            return queryset.filter(ip=input_value)

    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = ('id', 'user', 'ip', 'category', 'sub_category', 'action', 'result', 'start_date', 'end_date')


class AuditLogAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ['get']

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


class BankAccountFilter(filters.FilterSet):
    bank = filters.CharFilter(lookup_expr='icontains')
    account = filters.CharFilter(method='enc_account_filter')
    account_holder = filters.CharFilter(lookup_expr='icontains')

    def enc_account_filter(self, queryset, value, *args):
        return queryset.filter(account=make_enc_value(args[0]))

    class Meta:
        model = BankAccount
        fields = ('id', 'bank', 'account', 'account_holder', 'description')


class BankAccountAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.all()

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ['get']
    # http_method_names = ['get', 'post', 'put', 'delete']

    # 커스텀 필터 클래스 적용
    filterset_class = BankAccountFilter

    # 정렬 적용 필드
    ordering_fields = ['id', 'bank', 'account', 'account_holder', 'description']


class GuestBookFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    area = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = GuestBook
        fields = ('id', 'name', 'area', 'amount', 'attend', 'description', 'start_date', 'end_date')


class GuestBookAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = GuestBookSerializer
    queryset = GuestBook.objects.all()

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ['get']
    # http_method_names = ['get', 'post', 'put', 'delete']

    # 커스텀 필터 클래스 적용
    filterset_class = GuestBookFilter

    # 정렬 적용 필드
    ordering_fields = ['id', 'name', 'amount', 'area', 'attend', 'description']


class NoteFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    note = filters.CharFilter(method='enc_note_filter')

    def enc_note_filter(self, queryset, value, *args):
        return queryset.filter(note=make_enc_value(args[0]))

    start_date = filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Note
        fields = ('id', 'title', 'note', 'start_date', 'end_date')


class NoteAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = NoteSerializer
    queryset = Note.objects.all()

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ['get']
    # http_method_names = ['get', 'post', 'put', 'delete']

    # 커스텀 필터 클래스 적용
    filterset_class = NoteFilter

    # 정렬 적용 필드
    ordering_fields = ['id', 'title', 'note', 'date']


class SerialFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    value = filters.CharFilter(method='enc_value_filter')
    description = filters.CharFilter(method='enc_description_filter')

    def enc_value_filter(self, queryset, value, *args):
        return queryset.filter(value=make_enc_value(args[0]))

    def enc_description_filter(self, queryset, value, *args):
        return queryset.filter(description=make_enc_value(args[0]))

    class Meta:
        model = Serial
        fields = ('id', 'type', 'title', 'value', 'description')


class SerialAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = SerialSerializer
    queryset = Serial.objects.all()

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ['get']
    # http_method_names = ['get', 'post', 'put', 'delete']

    # 커스텀 필터 클래스 적용
    filterset_class = SerialFilter

    # 정렬 적용 필드
    ordering_fields = ['id', 'type', 'title', 'value', 'description']