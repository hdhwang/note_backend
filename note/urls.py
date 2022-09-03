from django.urls import path
from rest_framework import routers

from .views import AuditLogAPI

# View 구성에 ModelViewSet 클래스를 활용하는 경우 router를 통해 urlpattern을 자동으로 등록이 가능
router = routers.SimpleRouter(trailing_slash=False) # trailing_slash=False -> URL 후행 슬래시 제거
router.register('(?P<version>v([0-9])+)/audit-log', AuditLogAPI)

urlpatterns = router.urls + [
    # 추가할 URL 패턴이 존재하는 경우 여기에 추가
]