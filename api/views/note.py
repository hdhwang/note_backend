import logging

from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.response import Response

from utils.aes_helper import make_enc_value, get_dec_value
from utils.dic_helper import get_dic_value
from utils.format_helper import to_str
from utils.log_helper import insert_audit_log
from api.models import Note
from api.permissions import PermissionUser
from api.serializers import NoteSerializer

logger = logging.getLogger(__name__)

# 감사 로그 > 카테고리
category = "노트 관리"


class NoteFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr="icontains")
    note = filters.CharFilter(method="enc_note_filter")

    def enc_note_filter(self, queryset, name, value):
        return queryset.filter(note=make_enc_value(value))

    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    # 정렬 적용 필드 : (실제 필드, 파라미터 명)으로 기재
    ordering = filters.OrderingFilter(
        fields=(
            ("id", "id"),
            ("title", "title"),
            ("date", "date"),
        )
    )

    class Meta:
        model = Note
        fields = ("id", "title", "note", "start_date", "end_date")


class NoteAPI(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    queryset = Note.objects.all()
    permission_classes = [PermissionUser]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = NoteFilter

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
                if data.get("note"):
                    data["note"] = get_dec_value(data.get("note"))
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
            raise

        finally:
            # 감사 로그 기록
            actions.append(f"[제목] : {title}")
            audit_log = f"""추가 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, category, "-", audit_log, result
            )

    def update(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] : {get_dic_value(kwargs, 'pk')}""")

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
        actions.append(f"""[아이디] : {get_dic_value(kwargs, 'pk')}""")

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
            raise

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, category, "-", audit_log, result
            )
