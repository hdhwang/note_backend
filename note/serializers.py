from rest_framework import serializers

from .models import ChoiceResult, AuditLog, BankAccount, GuestBook, Note, Serial
from utils.formatHelper import *


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    ip = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    def get_user(self, obj):
        result = None
        if obj.user:
            result = obj.user.username

        return result

    def get_ip(self, obj):
        result = None
        if obj.ip:
            result = int_to_ip(obj.ip)

        return result

    def get_result(self, obj):
        result = 'Y' if obj.result == ChoiceYN.Y else 'N'

        return result

    def get_date(self, obj):
        result = ''
        if obj.date:
            result = datetime_to_str(obj.date, date_format='%Y-%m-%d %H:%M:%S')

        return result

    class Meta:
        model = AuditLog
        fields = '__all__'
        # fields = ('id', 'user', 'ip', 'category', 'sub_category', 'action', 'result', 'date')


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'


class GuestBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestBook
        fields = '__all__'


class NoteSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    def get_date(self, obj):
        result = ''
        if obj.date:
            result = datetime_to_str(obj.date)

        return result

    class Meta:
        model = Note
        fields = '__all__'


class SerialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serial
        fields = '__all__'