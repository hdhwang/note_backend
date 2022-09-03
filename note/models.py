from django.db import models
from django.contrib.auth.models import User


class ChoiceYN(models.IntegerChoices):
    Y = 1
    N = 0


class AuditLog(models.Model):
    user = models.ForeignKey(User, models.DO_NOTHING, db_column='user', blank=True, null=True)
    ip = models.PositiveIntegerField(blank=True, null=True)
    category = models.CharField(max_length=32, blank=True, null=True)
    sub_category = models.CharField(max_length=32, blank=True, null=True)
    action = models.TextField()
    result = models.IntegerField(
        choices=ChoiceYN.choices
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'


class BankAccount(models.Model):
    bank = models.CharField(max_length=256)
    account = models.CharField(max_length=512)
    account_holder = models.CharField(max_length=256)
    description = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'bank_account'
        unique_together = (('bank', 'account'),)


class GuestBook(models.Model):
    name = models.CharField(max_length=16, blank=True, null=True)
    amount = models.PositiveIntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    area = models.CharField(max_length=16, blank=True, null=True)
    attend = models.CharField(max_length=1)
    description = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'guest_book'


class Note(models.Model):
    title = models.CharField(max_length=512)
    note = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'note'


class Serial(models.Model):
    type = models.CharField(max_length=4)
    title = models.CharField(max_length=512)
    value = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'serial'
