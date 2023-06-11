from note import models
from utils.formatHelper import *
from utils.networkHelper import get_client_ip
import logging

logger = logging.getLogger(__name__)


def insert_audit_log(user, request, category, sub_category, action, result):
    try:
        log_result = False
        ip_int = (
            ip_to_int(get_client_ip(request))
            if type(ip_to_int(get_client_ip(request))) is int
            else None
        )

        audit_log_data = models.AuditLog(
            user=user,
            ip=ip_int,
            category=category,
            sub_category=sub_category,
            action=action,
            result=models.ChoiceResult.SUCCESS
            if result is True
            else models.ChoiceResult.FAIL,
        )
        audit_log_data.save()
        log_result = True

    except Exception as e:
        logger.warning(f"[insert_audit_log] {to_str(e)}")

    finally:
        return log_result
