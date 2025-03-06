import logging

from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.response import Response

from utils.aes_helper import make_enc_value, get_dec_value
from utils.dic_helper import get_dic_value
from utils.format_helper import to_str
from utils.log_helper import insert_audit_log
from api.models import BankAccount
from api.permissions import PermissionUser
from api.serializers import BankAccountSerializer

logger = logging.getLogger(__name__)

# 감사 로그 > 카테고리
category = "계좌번호 관리"


class BankAccountFilter(filters.FilterSet):
    bank = filters.CharFilter(lookup_expr="icontains")
    account = filters.CharFilter(method="enc_account_filter")
    account_holder = filters.CharFilter(lookup_expr="icontains")
    description = filters.CharFilter(method="enc_description_filter")

    def enc_account_filter(self, queryset, name, value):
        return queryset.filter(account=make_enc_value(value))

    def enc_description_filter(self, queryset, name, value):
        return queryset.filter(description=make_enc_value(value))

    # 정렬 적용 필드 : (실제 필드, 파라미터 명)으로 기재
    ordering = filters.OrderingFilter(
        fields=(
            ("id", "id"),
            ("bank", "bank"),
            ("account_holder", "account_holder"),
        )
    )

    class Meta:
        model = BankAccount
        fields = ("id", "bank", "account", "account_holder", "description")


class BankAccountAPI(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.all()
    permission_classes = [PermissionUser]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = BankAccountFilter

    def get_queryset(self):
        # 인증되지 않은 사용자는 빈 쿼리셋 반환
        if not self.request.user.is_authenticated:
            return super().get_queryset().none()

        # 인증된 사용자에 대해 필터링
        return super().get_queryset().filter(user=self.request.user)

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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
            raise

        finally:
            # 감사 로그 기록
            actions.append(f"[은행] : {bank}")
            actions.append(f"[예금주] : {account_holder}")
            audit_log = f"""추가 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, category, "-", audit_log, result
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
            raise

        finally:
            # 감사 로그 기록
            audit_log = f"""편집 ( {', '.join(actions)} )"""
            insert_audit_log(
                request.user.username, request, category, "-", audit_log, result
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
            raise

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, category, "-", audit_log, result
            )
