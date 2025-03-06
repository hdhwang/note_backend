import logging

from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.response import Response

from utils.dic_helper import get_dic_value
from utils.format_helper import to_str, to_int, datetime_to_str
from utils.log_helper import insert_audit_log
from api.models import GuestBook
from api.permissions import PermissionUser
from api.serializers import GuestBookSerializer

logger = logging.getLogger(__name__)

# 감사 로그 > 카테고리
category = "결혼식 방명록"


class GuestBookFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    area = filters.CharFilter(lookup_expr="icontains")
    description = filters.CharFilter(lookup_expr="icontains")

    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    # 정렬 적용 필드 : (실제 필드, 파라미터 명)으로 기재
    ordering = filters.OrderingFilter(
        fields=(
            ("id", "id"),
            ("name", "name"),
            ("amount", "amount"),
            ("area", "area"),
            ("attend", "attend"),
            ("description", "description"),
            ("date", "date"),
        )
    )

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
    serializer_class = GuestBookSerializer
    queryset = GuestBook.objects.all()
    permission_classes = [PermissionUser]

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = GuestBookFilter

    def get_queryset(self):
        # 인증되지 않은 사용자는 빈 쿼리셋 반환
        if not self.request.user.is_authenticated:
            return super().get_queryset().none()

        # 인증된 사용자에 대해 필터링
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []

        # 감사 로그 > 결과
        result = False

        try:
            name = get_dic_value(request.data, "name")
            amount = to_int(get_dic_value(request.data, "amount", None))
            date = get_dic_value(request.data, "date", None)
            area = get_dic_value(request.data, "area", "")
            attend = get_dic_value(request.data, "attend", "-")
            description = get_dic_value(request.data, "description", "")

            if amount is None:
                request.data['amount'] = None
            if date is None:
                request.data['date'] = None

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
            raise

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
                request.user.username, request, category, "-", audit_log, result
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
            area = get_dic_value(request.data, "area", "")
            attend = get_dic_value(request.data, "attend", "-")
            description = get_dic_value(request.data, "description", "")

            if amount is None:
                request.data['amount'] = None
            if date is None:
                request.data['date'] = None

            partial = kwargs.pop("partial", False)
            instance = self.get_object()

            if instance.name != name:
                # 감사 로그 > 내용 추가
                actions.append(f"[이름] {instance.name} → {name}")

            if instance.amount != amount:
                org_amount_str = instance.amount if instance.amount is not None else ""
                amount_str = amount if amount is not None else ""

                # 감사 로그 > 내용 추가
                actions.append(f"[금액] {org_amount_str} → {amount_str}")

            org_date_str = datetime_to_str(instance.date, "%Y-%m-%d") if instance.date else ""
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
            raise

        finally:
            # 감사 로그 기록
            audit_log = f"""삭제 ( {', '.join(actions)} )"""

            insert_audit_log(
                request.user.username, request, category, "-", audit_log, result
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