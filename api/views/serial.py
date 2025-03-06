import logging

from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.response import Response

from utils.aes_helper import make_enc_value, get_dec_value
from utils.dic_helper import get_dic_value
from utils.format_helper import to_str
from utils.log_helper import insert_audit_log
from api.models import Serial
from api.permissions import PermissionUser
from api.serializers import SerialSerializer

logger = logging.getLogger(__name__)


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
    serializer_class = SerialSerializer
    queryset = Serial.objects.all()
    permission_classes = [PermissionUser]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = SerialFilter

    # 정렬 적용 필드
    ordering_fields = ["id", "type", "title"]

    # 감사 로그 > 카테고리
    category = "시리얼 번호 관리"

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
                if data.get("value"):
                    data["value"] = get_dec_value(data.get("value"))

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
            raise

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
            raise

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
            raise

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, self.category, "-", audit_log, result
            )
