from django.contrib.auth.models import User
from rest_framework import serializers
from .models import AuditLog, BankAccount, GuestBook, Note, Serial
from utils.formatHelper import *


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('password', 'new_password')


class AuditLogSerializer(serializers.ModelSerializer):
    ip = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    def get_ip(self, obj):
        result = None
        if obj.ip:
            result = int_to_ip(obj.ip)

        return result

    def get_result(self, obj):
        return obj.get_result_display()

    def get_date(self, obj):
        result = ""
        if obj.date:
            result = datetime_to_str(obj.date, date_format="%Y-%m-%d %H:%M:%S")

        return result

    class Meta:
        model = AuditLog
        fields = "__all__"
        # fields = ('id', 'user', 'ip', 'category', 'sub_category', 'action', 'result', 'date')


class BankAccountSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = BankAccount
        fields = "__all__"


class GuestBookSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = GuestBook
        fields = "__all__"


class NoteSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    user = serializers.ReadOnlyField(source="user.username")

    def get_date(self, obj):
        result = ""
        if obj.date:
            result = datetime_to_str(obj.date)

        return result

    class Meta:
        model = Note
        fields = "__all__"


class SerialSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Serial
        fields = "__all__"
