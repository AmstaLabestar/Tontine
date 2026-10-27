from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id", "group", "event_type", "actor", "actor_name",
            "target_type", "target_id", "description", "metadata",
            "ip_address", "device_id", "created_at",
        ]
        read_only_fields = fields

