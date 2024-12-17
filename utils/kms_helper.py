import json
import logging
import os

import requests

from utils.format_helper import *

logger = logging.getLogger(__name__)


def get_kms_value():
    result = {}

    try:
        kms_info = get_server_info_value("kms")
        key = kms_info.get("key")
        token = kms_info.get("token")
        url = kms_info.get("url")

        data = {"key": f"{key}"}
        headers = {"Authorization": f"Token {token}"}
        response = requests.get(url, params=data, headers=headers, verify=False)
        if response.status_code == 200 and response.json()["data"]:
            result = response.json()["data"][0]["value"]

    except Exception as e:
        logger.warning(f"[get_kms_value] {to_str(e)}")

    finally:
        return result


def get_server_info_value(key: str):
    with open(
        os.path.dirname(os.path.abspath(__file__)) + "/kms.json",
        mode="rt",
        encoding="utf-8",
    ) as file:
        data = json.load(file)
        for k, v in data.items():
            if k == key:
                return v
            raise ValueError("Could not verify server information.")
