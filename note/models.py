from django.db import models
from django.contrib.auth.models import User


def choice_str_to_int(choice_class, input_value):
    for num, string in choice_class.choices:
        if string.upper() == input_value.upper():
            return num
    return None


class ChoiceResult(models.IntegerChoices):
    SUCCESS = 1, "성공"
    FAIL = 0, "실패"


class AuditLog(models.Model):
    user = models.CharField(max_length=128, blank=True, null=True)
    ip = models.PositiveIntegerField(blank=True, null=True)
    category = models.CharField(max_length=32, blank=True, null=True)
    sub_category = models.CharField(max_length=32, blank=True, null=True)
    action = models.TextField()
    result = models.IntegerField(choices=ChoiceResult.choices)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["id"]


class BankAccount(models.Model):
    bank = models.CharField(max_length=256)
    account = models.CharField(max_length=512)
    account_holder = models.CharField(max_length=256)
    description = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = "bank_account"
        unique_together = (("bank", "account"),)
        ordering = ["id"]


class GuestBook(models.Model):
    name = models.CharField(max_length=16, blank=True, null=True)
    amount = models.PositiveIntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    area = models.CharField(max_length=16, blank=True, null=True)
    attend = models.CharField(max_length=1)
    description = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        db_table = "guest_book"
        ordering = ["id"]


class Note(models.Model):
    title = models.CharField(max_length=512)
    note = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "note"
        ordering = ["id"]


class Serial(models.Model):
    type = models.CharField(max_length=4)
    title = models.CharField(max_length=512)
    value = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = "serial"
        ordering = ["id"]
