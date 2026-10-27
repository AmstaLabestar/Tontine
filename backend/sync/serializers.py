from rest_framework import serializers

from .models import Device, SyncOperation, SyncCursor


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            "id", "device_id", "user", "group", "name", "platform",
            "status", "last_sync_at", "last_sync_cursor", "registered_at",
        ]
        read_only_fields = ["id", "registered_at", "last_sync_at", "last_sync_cursor"]


class SyncOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncOperation
        fields = [
            "id", "idempotency_key", "device", "group", "operation_type",
            "payload", "status", "conflict_reason", "server_timestamp",
            "resolved_at",
        ]
        read_only_fields = ["id", "server_timestamp", "resolved_at"]


class SyncPushSerializer(serializers.Serializer):
    """Serializer for pushing local operations to server."""
    operations = serializers.ListField(child=serializers.DictField())

    def validate_operations(self, value):
        if not value:
            raise serializers.ValidationError("Operations list cannot be empty.")
        return value


class SyncPullSerializer(serializers.Serializer):
    """Serializer for pulling remote operations."""
    cursor = serializers.CharField(default="0")
    limit = serializers.IntegerField(default=100, max_value=500)
