from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        # fields = ('id', 'user', 'ip', 'category', 'sub_category', 'action', 'result', 'date')