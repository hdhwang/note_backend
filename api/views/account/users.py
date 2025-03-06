import logging

from django.contrib.auth.models import User, Group
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.response import Response

from api import message
from api.models import ChoiceAccountStatus
from api.permissions import PermissionAdmin
from api.serializers import UsersSerializer
from utils.dic_helper import get_dic_value
from utils.format_helper import to_str, choice_str_to_int
from utils.log_helper import insert_audit_log
from utils.network_helper import get_client_ip

logger = logging.getLogger(__name__)

# 감사 로그 > 카테고리
category = '계정 관리'
sub_category = '사용자 관리'


class UsersFilter(filters.FilterSet):
    status_list = [list(reversed(choice_account_status)) for choice_account_status in list(ChoiceAccountStatus.choices)]
    permission_list = [(group.name, group.name) for group in Group.objects.all()]

    user_id = filters.filters.CharFilter(field_name='username', lookup_expr='icontains')
    name = filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    email = filters.CharFilter(field_name='email', lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=status_list, method='status_filter', help_text=f'Available values : {", ".join(list(zip(*ChoiceAccountStatus.choices))[1])}')
    permission = filters.ChoiceFilter(choices=permission_list, method='permission_filter', help_text=f'Available values : {", ".join([perm[0] for perm in permission_list])}')

    def status_filter(self, queryset, name, value):
        return queryset.filter(is_active=choice_str_to_int(ChoiceAccountStatus, value))

    def permission_filter(self, queryset, name, value):
        return queryset.filter(groups__name=value)

    # 정렬 적용 필드 : (실제 필드, 파라미터 명)으로 기재
    ordering = filters.OrderingFilter(
        fields = (
            ('id', 'id'),
            ('username', 'user_id'),
            ('first_name', 'name'),
            ('email', 'email'),
            ('is_active', 'status'),
            ('groups', 'permission'),
            ('date_joined', 'created_at'),
            ('last_login', 'last_login'),
        )
    )

    class Meta:
        model = User
        fields = ['user_id', 'name', 'email', 'status', 'permission']


class UsersAPI(viewsets.ModelViewSet):
    serializer_class = UsersSerializer
    permission_classes = [PermissionAdmin]
    queryset = User.objects.all().defer('password').order_by('id')

    # 지원 HTTP 메소드 설정 (CRUD)
    http_method_names = ["get", "post", "put", "delete"]

    # 커스텀 필터 클래스 적용
    filterset_class = UsersFilter

    def create(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []

        # 감사 로그 > 결과
        result = False

        user_id = ''
        name = ''
        email = ''
        user_status = ''
        permission = ''

        try:
            user_id = request.data.get('user_id', '')
            password = request.data.get('password', '')
            name = request.data.get('name', '')
            email = request.data.get('email', '')
            user_status = request.data.get('user_status', '')
            permission = request.data.get('permission', '')

            if not user_id or not password or not name or not email or not user_status or not permission:
                data = []
                if not user_id:
                    data.append({'user_id': [message.required_field]})
                if not password:
                    data.append({'password': [message.required_field]})
                if not name:
                    data.append({'name': [message.required_field]})
                if not email:
                    data.append({'email': [message.required_field]})
                if not user_status:
                    data.append({'user_status': [message.required_field]})
                if not permission:
                    data.append({'permission': [message.required_field]})
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(id=user_id).exists():
                return Response({'user_id': [message.duplicated]}, status=status.HTTP_409_CONFLICT)

            if permission not in ['사용자', '관리자']:
                return Response({'permission': [message.invalid_permission_field]}, status=status.HTTP_400_BAD_REQUEST)

            if not Group.objects.filter(name=permission).exists():
                return Response({'permission': [message.not_found]}, status=status.HTTP_404_NOT_FOUND)

            user = User.objects.create_user(user_id, email, password)
            user.is_active = True if user_status == '활성화' else False
            user.is_staff = False
            user.is_superuser = False
            user.first_name = name
            user.groups.add(Group.objects.get(name=permission))
            user.save()
            result = True

            return Response({
                'id': user.id,
                'user_id': user.username,
                'name': user.first_name,
                'email': user.email,
                'status': '활성화' if user.is_active else '비활성화',
                'permission': list(Group.objects.filter(user__id=user.id).values_list('name', flat=True)),
                'created_at': user.date_joined,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.warning(f'[UsersAPI - create] {to_str(e)}')
            raise

        finally:
            # 감사 로그 기록
            actions.append(f'[사용자 아이디] : {user_id}')
            actions.append(f'[이름] : {name}')
            actions.append(f'[이메일] : {email}')
            actions.append(f'[상태] : {user_status}')
            actions.append(f'[권한] : {permission}')
            audit_log = f"""사용자 생성 ( {', '.join(actions)} )"""

            insert_audit_log(request.user.username, get_client_ip(request), category, sub_category, audit_log, result)

    def update(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] : {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            user = User.objects.get(id=kwargs['pk']) if User.objects.filter(id=kwargs['pk']).exists() else None
            if not user:
                return Response({'user_id': message.not_found}, status=status.HTTP_404_NOT_FOUND)

            password = request.data.get('password', '')
            name = request.data.get('name', '')
            email = request.data.get('email', '')
            is_active = True if request.data.get('is_active') == '활성화' else False
            permission = request.data.get('permission', '')

            # 감사 로그 > 내용 추가
            actions.append(f'[사용자 아이디] : {user.username}')

            if name and user.first_name != name:
                # 감사 로그 > 내용 추가
                actions.append(f"[이름] : {user.first_name} → {name}")

                user.first_name = name

            if email and user.email != email:
                # 감사 로그 > 내용 추가
                actions.append(f"[이메일] : {user.email} → {email}")

                user.email = email

            if user.is_active != is_active:
                org_user_status = '활성화' if user.is_active else '비활성화'
                user_status = '활성화' if is_active else '비활성화'

                # 감사 로그 > 내용 추가
                actions.append(f"[상태] : {org_user_status} → {user_status}")

                user.is_active = is_active

            # 권한 변경 추가 필요
            # 비밀번호 변경 추가 필요

            user.save()
            result = True

            return Response({
                'id': user.id,
                'user_id': user.username,
                'name': user.first_name,
                'email': user.email,
                'status': '활성화' if user.is_active else '비활성화',
                'permission': list(Group.objects.filter(user__id=user.id).values_list('name', flat=True)),
                'created_at': user.date_joined,
                'last_login': user.last_login,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.warning(f'[UsersAPI - update] {to_str(e)}')
            raise

        finally:
            # 감사 로그 기록
            audit_log = f"""사용자 편집 ( {', '.join(actions)} )"""
            insert_audit_log(request.user.username, get_client_ip(request), category, sub_category, audit_log, result)

    def destroy(self, request, *args, **kwargs):
        # 감사 로그 > 내용
        actions = []
        actions.append(f"""[아이디] : {get_dic_value(kwargs, 'pk')}""")

        # 감사 로그 > 결과
        result = False

        try:
            user = User.objects.get(id=kwargs['pk']) if User.objects.filter(id=kwargs['pk']).exists() else None
            if not user:
                return Response({'user_id': message.not_found}, status=status.HTTP_404_NOT_FOUND)

            actions.append(f"""[사용자 아이디] : {user.first_name}""")
            actions.append(f"""[이름] : {user.first_name}""")
            actions.append(f"""[이메일] : {user.email}""")
            actions.append(f"""[상태] : {'활성화' if user.is_active is True else '비활성화'}""")
            actions.append(f"""[권한] : {list(Group.objects.filter(user__id=user.id).values_list('name', flat=True))}""")

            if user == request.user:
                return Response('본인의 계정은 삭제할 수 없습니다.', status=status.HTTP_400_BAD_REQUEST)

            user.delete()
            result = True
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.warning(f'[UsersAPI - destroy] {to_str(e)}')
            raise

        finally:
            # 감사 로그 기록
            audit_log = f"""사용자 삭제 ( {', '.join(actions)} )"""
            insert_audit_log(request.user.username, get_client_ip(request), category, sub_category, audit_log, result)
