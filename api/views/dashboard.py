import logging

from rest_framework import viewsets, status
from rest_framework.response import Response

from api.models import BankAccount, GuestBook, Note, Serial
from api.permissions import PermissionUser
from api.serializers import DashboardStatsSerializer

logger = logging.getLogger(__name__)


class DashboardStatsAPI(viewsets.ViewSet):
    permission_classes = [PermissionUser]
    serializer_class = DashboardStatsSerializer

    def list(self, request, *args, **kwargs):
        data = {
            "bank_account_count": BankAccount.objects.count(),
            "guest_book_count": GuestBook.objects.count(),
            "note_count": Note.objects.count(),
            "serial_count": Serial.objects.count(),
        }

        return Response(data, status=status.HTTP_200_OK)
