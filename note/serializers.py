from rest_framework import serializers

from .models import ChoiceYN, AuditLog, BankAccount, GuestBook, Note, Serial
from utils.AESHelper import get_dec_value


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    def get_user(self, obj):
        result = None
        if obj.user:
            result = obj.user.username

        return result

    def get_result(self, obj):
        result = 'Y' if obj.result is ChoiceYN.Y else 'N'

        return result

    class Meta:
        model = AuditLog
        fields = '__all__'
        # fields = ('id', 'user', 'ip', 'category', 'sub_category', 'action', 'result', 'date')


class BankAccountSerializer(serializers.ModelSerializer):
    account = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_account(self, obj):
        return get_dec_value(obj.account)

    def get_description(self, obj):
        return get_dec_value(obj.description)

    class Meta:
        model = BankAccount
        fields = '__all__'


class GuestBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestBook
        fields = '__all__'


class NoteSerializer(serializers.ModelSerializer):
    note = serializers.SerializerMethodField()

    def get_note(self, obj):
        return get_dec_value(obj.note)

    class Meta:
        model = Note
        fields = '__all__'


class SerialSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_value(self, obj):
        return get_dec_value(obj.value)

    def get_description(self, obj):
        return get_dec_value(obj.description)

    class Meta:
        model = Serial
        fields = '__all__'