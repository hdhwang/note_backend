import logging
import random

from rest_framework import viewsets, status
from rest_framework.response import Response

from utils.format_helper import to_str
from api.permissions import PermissionUser
from api.serializers import LottoSerializer

logger = logging.getLogger(__name__)


class LottoAPI(viewsets.ModelViewSet):
    filter_backends = []
    pagination_class = None
    serializer_class = LottoSerializer
    permission_classes = [PermissionUser]

    def list(self, request, *args, **kwargs):
        data = self.gen_lotto()
        return Response(data, status=status.HTTP_200_OK)

    def gen_lotto(self):
        result = []

        try:
            for i in range(5):
                num_list = []
                ran_num = random.randint(1, 45)
                for j in range(6):
                    while ran_num in num_list:
                        ran_num = random.randint(1, 45)
                    num_list.append(ran_num)

                num_list.sort()
                str_num_list = ''

                for k in range(6):
                    str_num = '%02d' % num_list[k]
                    str_num_list += str_num if str_num_list == '' else f' {str_num}'

                result.append({"num": chr(i + 65), "value": str_num_list})

        except Exception as e:
            logger.warning(f"[LottoAPI - gen_lotto] {to_str(e)}")
            raise

        return result
