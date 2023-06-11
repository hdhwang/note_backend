from .models import *
from .serializers import *
from .permissions import PermissionUser, PermissionAdmin, PermissionSuperUser

from bs4 import BeautifulSoup
from django_filters import rest_framework as filters
from rest_framework import viewsets, versioning, status
from rest_framework.response import Response
from utils.AESHelper import make_enc_value, get_dec_value
from utils.dicHelper import get_dic_value
from utils.formatHelper import *
from utils.logHelper import insert_audit_log
from utils.regexHelper import *

import random
import requests

import logging

logger = logging.getLogger(__name__)


class CustomURLPathVersioning(versioning.URLPathVersioning):
    allowed_versions = ["v1"]


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
    versioning_class = CustomURLPathVersioning
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


class BankAccountFilter(filters.FilterSet):
    bank = filters.CharFilter(lookup_expr="icontains")
    account = filters.CharFilter(method="enc_account_filter")
    account_holder = filters.CharFilter(lookup_expr="icontains")
    description = filters.CharFilter(method="enc_description_filter")

    def enc_account_filter(self, queryset, name, value):
        return queryset.filter(account=make_enc_value(value))

    def enc_description_filter(self, queryset, name, value):
        return queryset.filter(description=make_enc_value(value))

    class Meta:
        model = BankAccount
        fields = ("id", "bank", "account", "account_holder", "description")


class BankAccountAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.all()
    permission_classes = [PermissionAdmin]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = BankAccountFilter

    # 정렬 적용 필드
    ordering_fields = ["id", "bank", "account_holder"]

    # 감사 로그 > 카테고리
    category = "계좌번호 관리"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for data in serializer.data:
                if data.get("account"):
                    data["account"] = get_dec_value(data.get("account"))

                if data.get("description"):
                    data["description"] = get_dec_value(data.get("description"))
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []

        # 감사 로그 > 결과
        result = False

        try:
            bank = get_dic_value(request.data, "bank")
            account_holder = get_dic_value(request.data, "account_holder")

            if request.data.get("account"):
                request.data["account"] = make_enc_value(request.data.get("account"))

            if request.data.get("description"):
                request.data["description"] = make_enc_value(
                    request.data.get("description")
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # 추가 성공 시 감사 로그 > 내용에 아이디 항목 추가
            actions.append(f'[아이디] : {to_str(serializer.data.get("id"))}')

            result = True
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

        except Exception as e:
            logger.warning(f"[BankAccountAPI - create] {to_str(e)}")

        finally:
            # 감사 로그 기록
            actions.append(f"[은행] : {bank}")
            actions.append(f"[예금주] : {account_holder}")
            audit_log = f"""추가 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def update(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            if request.data.get("account"):
                request.data["account"] = make_enc_value(request.data.get("account"))

            if request.data.get("description"):
                request.data["description"] = make_enc_value(
                    request.data.get("description")
                )

            bank = get_dic_value(request.data, "bank")
            account_holder = get_dic_value(request.data, "account_holder")

            partial = kwargs.pop("partial", False)
            instance = self.get_object()

            if instance.bank != bank:
                # 감사 로그 > 내용 추가
                actions.append(f"[은행] {instance.bank} → {bank}")

            if instance.account != get_dic_value(request.data, "account"):
                # 감사 로그 > 내용 추가
                actions.append(f"[계좌번호 변경]")

            if instance.account_holder != account_holder:
                # 감사 로그 > 내용 추가
                actions.append(f"[예금주] {instance.account_holder} → {account_holder}")

            if instance.description != get_dic_value(request.data, "description"):
                # 감사 로그 > 내용 추가
                actions.append(f"[설명 변경]")

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, "_prefetched_objects_cache", None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            result = True
            return Response(serializer.data)

        except Exception as e:
            logger.warning(f"[BankAccountAPI - update] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""편집 ( {', '.join(actions)} )"""
            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def destroy(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            instance = self.get_object()
            actions.append(f"[은행] : {to_str(instance.bank)}")
            actions.append(f"[예금주] : {to_str(instance.account_holder)}")

            self.perform_destroy(instance)

            result = True
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.warning(f"[BankAccountAPI - destroy] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )


class GuestBookFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    area = filters.CharFilter(lookup_expr="icontains")
    description = filters.CharFilter(lookup_expr="icontains")

    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = GuestBook
        fields = (
            "id",
            "name",
            "area",
            "amount",
            "attend",
            "description",
            "start_date",
            "end_date",
        )


class GuestBookAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = GuestBookSerializer
    queryset = GuestBook.objects.all()
    permission_classes = [PermissionAdmin]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = GuestBookFilter

    # 정렬 적용 필드
    ordering_fields = ["id", "name", "amount", "area", "attend", "description"]

    # 감사 로그 > 카테고리
    category = "결혼식 방명록"

    def create(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []

        # 감사 로그 > 결과
        result = False

        try:
            name = get_dic_value(request.data, "name")
            amount = to_int(get_dic_value(request.data, "amount", None))
            date = get_dic_value(request.data, "date", None)
            area = get_dic_value(request.data, "area")
            attend = get_dic_value(request.data, "attend", "-")
            description = get_dic_value(request.data, "description")

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # 추가 성공 시 감사 로그 > 내용에 아이디 항목 추가
            actions.append(f'[아이디] : {to_str(serializer.data.get("id"))}')

            result = True
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

        except Exception as e:
            logger.warning(f"[GuestBookAPI - create] {to_str(e)}")

        finally:
            date_str = date if date is not None else ""
            amount_str = to_str(amount) if amount is not None else ""

            # 감사 로그 기록
            actions.append(f"[이름] : {name}")
            actions.append(f"[금액] : {amount_str}")
            actions.append(f"[일자] : {date_str}")
            actions.append(f"[장소] : {area}")
            actions.append(f"[참석 여부] : {self.get_attend_str(attend)}")
            actions.append(f"[설명] : {description}")
            audit_log = f"""추가 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def update(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            name = get_dic_value(request.data, "name")
            amount = to_int(get_dic_value(request.data, "amount", None))
            date = get_dic_value(request.data, "date", None)
            area = get_dic_value(request.data, "area")
            attend = get_dic_value(request.data, "attend", "-")
            description = get_dic_value(request.data, "description")

            partial = kwargs.pop("partial", False)
            instance = self.get_object()

            if instance.name != name:
                # 감사 로그 > 내용 추가
                actions.append(f"[이름] {instance.name} → {name}")

            if instance.amount != amount:
                # 감사 로그 > 내용 추가
                actions.append(f"[금액] {instance.amount} → {amount}")

            org_date_str = (
                datetime_to_str(instance.date, "%Y-%m-%d") if instance.date else ""
            )
            date_str = date if date is not None else ""
            if org_date_str != date_str:
                # 감사 로그 > 내용 추가
                actions.append(f"[일자] {org_date_str} → {date_str}")

            if instance.area != area:
                # 감사 로그 > 내용 추가
                actions.append(f"[장소] {instance.area} → {area}")

            if instance.attend != attend:
                # 감사 로그 > 내용 추가
                actions.append(
                    f"[참석 여부] {self.get_attend_str(instance.attend)} → {self.get_attend_str(attend)}"
                )

            if instance.description != get_dic_value(request.data, "description"):
                # 감사 로그 > 내용 추가
                actions.append(f"[설명] {instance.description} → {description}")

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, "_prefetched_objects_cache", None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            result = True
            return Response(serializer.data)

        except Exception as e:
            logger.warning(f"[GuestBookAPI - update] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""편집 ( {', '.join(actions)} )"""
            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def destroy(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            instance = self.get_object()
            actions.append(f"[이름] : {instance.name}")
            actions.append(
                f"""[금액] : {to_str(instance.amount) if instance.amount else ''}"""
            )
            actions.append(
                f"""[일자] : {datetime_to_str(instance.date, '%Y-%m-%d') if instance.date else ''}"""
            )
            actions.append(f"[장소] : {instance.area}")
            actions.append(f"[참석 여부] : {self.get_attend_str(instance.attend)}")
            actions.append(f"[설명] : {instance.description}")

            self.perform_destroy(instance)

            result = True
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.warning(f"[GuestBookAPI - destroy] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def get_attend_str(self, data):
        result = ""
        if data == "Y":
            result = "참석"

        elif data == "N":
            result = "미참석"

        elif data == "-":
            result = "미정"

        return result


class NoteFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr="icontains")
    note = filters.CharFilter(method="enc_note_filter")

    def enc_note_filter(self, queryset, name, value):
        return queryset.filter(note=make_enc_value(value))

    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Note
        fields = ("id", "title", "note", "start_date", "end_date")


class NoteAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = NoteSerializer
    queryset = Note.objects.all()
    permission_classes = [PermissionAdmin]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = NoteFilter

    # 정렬 적용 필드
    ordering_fields = ["id", "title", "date"]

    # 감사 로그 > 카테고리
    category = "노트 관리"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for data in serializer.data:
                if data.get("note"):
                    data["note"] = get_dec_value(data.get("note"))
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []

        # 감사 로그 > 결과
        result = False

        try:
            title = get_dic_value(request.data, "title")

            if request.data.get("note"):
                request.data["note"] = make_enc_value(request.data.get("note"))

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # 추가 성공 시 감사 로그 > 내용에 아이디 항목 추가
            actions.append(f'[아이디] : {to_str(serializer.data.get("id"))}')

            result = True
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

        except Exception as e:
            logger.warning(f"[NoteAPI - create] {to_str(e)}")

        finally:
            # 감사 로그 기록
            actions.append(f"[제목] : {title}")
            audit_log = f"""추가 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def update(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            if request.data.get("note"):
                request.data["note"] = make_enc_value(request.data.get("note"))

            title = get_dic_value(request.data, "title")

            partial = kwargs.pop("partial", False)
            instance = self.get_object()

            if instance.title != title:
                # 감사 로그 > 내용 추가
                actions.append(f"[제목] {instance.title} → {title}")

            if instance.note != get_dic_value(request.data, "note"):
                # 감사 로그 > 내용 추가
                actions.append(f"[내용 변경]")

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, "_prefetched_objects_cache", None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            result = True
            return Response(serializer.data)

        except Exception as e:
            logger.warning(f"[NoteAPI - update] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""편집 ( {', '.join(actions)} )"""
            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def destroy(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            instance = self.get_object()
            actions.append(f"[제목] : {to_str(instance.title)}")

            self.perform_destroy(instance)

            result = True
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.warning(f"[NoteAPI - destroy] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )


class SerialFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr="icontains")
    value = filters.CharFilter(method="enc_value_filter")
    description = filters.CharFilter(method="enc_description_filter")

    def enc_value_filter(self, queryset, name, value):
        return queryset.filter(value=make_enc_value(value))

    def enc_description_filter(self, queryset, name, value):
        return queryset.filter(description=make_enc_value(value))

    class Meta:
        model = Serial
        fields = ("id", "type", "title", "value", "description")


class SerialAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    serializer_class = SerialSerializer
    queryset = Serial.objects.all()
    permission_classes = [PermissionAdmin]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = SerialFilter

    # 정렬 적용 필드
    ordering_fields = ["id", "type", "title"]

    # 감사 로그 > 카테고리
    category = "시리얼 번호 관리"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for data in serializer.data:
                if data.get("value"):
                    data["value"] = get_dec_value(data.get("value"))

                if data.get("description"):
                    data["description"] = get_dec_value(data.get("description"))
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []

        # 감사 로그 > 결과
        result = False

        try:
            serial_type = get_dic_value(request.data, "type")
            title = get_dic_value(request.data, "title")

            if request.data.get("value"):
                request.data["value"] = make_enc_value(request.data.get("value"))

            if request.data.get("description"):
                request.data["description"] = make_enc_value(
                    request.data.get("description")
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # 추가 성공 시 감사 로그 > 내용에 아이디 항목 추가
            actions.append(f'[아이디] : {to_str(serializer.data.get("id"))}')

            result = True
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

        except Exception as e:
            logger.warning(f"[SerialAPI - create] {to_str(e)}")

        finally:
            # 감사 로그 기록
            actions.append(f"[유형] : {serial_type}")
            actions.append(f"[제품 명] : {title}")
            audit_log = f"""추가 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def update(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            if request.data.get("value"):
                request.data["value"] = make_enc_value(request.data.get("value"))

            if request.data.get("description"):
                request.data["description"] = make_enc_value(
                    request.data.get("description")
                )

            serial_type = get_dic_value(request.data, "type")
            title = get_dic_value(request.data, "title")

            partial = kwargs.pop("partial", False)
            instance = self.get_object()

            if instance.type != serial_type:
                # 감사 로그 > 내용 추가
                actions.append(f"[유형] {instance.type} → {serial_type}")

            if instance.title != title:
                # 감사 로그 > 내용 추가
                actions.append(f"[제품 명] {instance.title} → {title}")

            if instance.value != get_dic_value(request.data, "value"):
                # 감사 로그 > 내용 추가
                actions.append(f"[시리얼 번호 변경]")

            if instance.description != get_dic_value(request.data, "description"):
                # 감사 로그 > 내용 추가
                actions.append(f"[설명 변경]")

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, "_prefetched_objects_cache", None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            result = True
            return Response(serializer.data)

        except Exception as e:
            logger.warning(f"[SerialAPI - update] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""편집 ( {', '.join(actions)} )"""
            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )

    def destroy(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            instance = self.get_object()
            actions.append(f"[유형] : {to_str(instance.type)}")
            actions.append(f"[제품 명] : {to_str(instance.title)}")

            self.perform_destroy(instance)

            result = True
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.warning(f"[SerialAPI - destroy] {to_str(e)}")

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )


class LottoAPI(viewsets.ModelViewSet):
    versioning_class = CustomURLPathVersioning
    filter_backends = []
    pagination_class = None
    permission_classes = [PermissionUser]

    def list(self, request, *args, **kwargs):
        data = self.gen_lotto_by_statistics()
        return Response(data, status=status.HTTP_200_OK)

    def gen_lotto_by_statistics(self):
        result = []

        try:
            base_url = "https://dhlottery.co.kr/gameResult.do?method=statByNumber"
            con = requests.get(base_url)
            soup = BeautifulSoup(con.content, "html.parser")
            stats_table = soup.find("table", {"class": "tbl_data tbl_data_col"})

            stats_list = []
            ball_list = []

            for tr in stats_table.find_all("tr"):
                ball_data = []
                for td in tr.find_all("td"):
                    data = td.get_text()
                    if "\n\n" not in data:
                        ball_data.append(int(data))

                if ball_data:
                    stats_list.append(ball_data)

            for stats in stats_list:
                number = stats[0]
                count = stats[1]

                for i in range(count):
                    ball_list.append(number)

            random.shuffle(ball_list)

            for i in range(5):
                num_list = []
                str_num_list = ""

                for j in range(6):
                    lotto = random.choice(ball_list)
                    while lotto in num_list:
                        lotto = random.choice(ball_list)
                    num_list.append(lotto)

                num_list.sort()

                for j in range(6):
                    str_num = "%02d" % int(num_list[j])
                    str_num_list += str_num if str_num_list == "" else f", {str_num}"

                result.append({"num": chr(i + 65), "value": str_num_list})

        except Exception as e:
            logger.warning(f"[LottoAPI - gen_lotto_by_statistics] {to_str(e)}")

        return result
