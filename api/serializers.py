from django.contrib.auth.models import User, Group
from rest_framework import serializers

from utils.format_helper import int_to_ip, datetime_to_str
from .models import AuditLog, BankAccount, GuestBook, Note, Serial


class DashboardStatsSerializer(serializers.Serializer):
    bank_account_count = serializers.IntegerField()
    guest_book_count = serializers.IntegerField()
    note_count = serializers.IntegerField()
    serial_count = serializers.IntegerField()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('password', 'new_password')


class UsersSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        return obj.username

    def get_name(self, obj):
        return obj.first_name

    def get_status(self, obj):
        return '활성화' if obj.is_active else '비활성화'

    def get_permission(self, obj):
        return Group.objects.filter(user=obj).values_list('name', flat=True)

    def get_created_at(self, obj):
        result = ""
        if obj.date_joined:
            result = datetime_to_str(obj.date_joined, date_format="%Y-%m-%d %H:%M:%S")

        return result

    def get_last_login(self, obj):
        result = ""
        if obj.last_login:
            result = datetime_to_str(obj.last_login, date_format="%Y-%m-%d %H:%M:%S")

        return result

    class Meta:
        model = User
        fields = ('id', 'user_id', 'name', 'email', 'status', 'permission', 'created_at', 'last_login')


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


class LottoSerializer(serializers.Serializer):
    num = serializers.CharField()
    value = serializers.CharField()
