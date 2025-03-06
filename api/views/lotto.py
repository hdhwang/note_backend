import logging
import random

import requests
from bs4 import BeautifulSoup
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
            raise

        return result
