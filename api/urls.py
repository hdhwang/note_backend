from django.urls import re_path
from rest_framework import routers

from api.views import (
    audit_log,
    bank_account,
    dashboard,
    guest_book,
    lotto,
    note,
    serial,
)
from api.views.account import (
    user,
)

# View 구성에 ModelViewSet 클래스를 활용하는 경우 router를 통해 urlpattern을 자동으로 등록이 가능
router = routers.SimpleRouter(
    trailing_slash=False
)  # trailing_slash=False -> URL 후행 슬래시 제거
router.register("(?P<version>v([0-9])+)/dashboard/stats", dashboard.DashboardStatsAPI, basename='dashboard-stats')
router.register("(?P<version>v([0-9])+)/audit-log", audit_log.AuditLogAPI)
router.register("(?P<version>v([0-9])+)/bank-account", bank_account.BankAccountAPI)
router.register("(?P<version>v([0-9])+)/guest-book", guest_book.GuestBookAPI)
router.register("(?P<version>v([0-9])+)/note", note.NoteAPI)
router.register("(?P<version>v([0-9])+)/serial", serial.SerialAPI)

urlpatterns = router.urls + [
    # 추가할 URL 패턴이 존재하는 경우 여기에 추가
    re_path("(?P<version>v([0-9])+)/lotto", lotto.LottoAPI.as_view({"get": "list"})),
    re_path("(?P<version>v([0-9])+)/account/user", user.AccountUserAPI.as_view({"put": "update"})),
]
