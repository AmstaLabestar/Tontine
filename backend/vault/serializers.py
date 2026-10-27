from rest_framework import serializers

from .models import VaultVerification


class VaultVerificationSerializer(serializers.ModelSerializer):
    counted_by_name = serializers.CharField(source="counted_by.display_name", read_only=True)
    verified_by_name = serializers.CharField(source="verified_by.display_name", read_only=True)

    class Meta:
        model = VaultVerification
        fields = [
            "id", "group", "counted_by", "counted_by_name",
            "verified_by", "verified_by_name", "physical_amount",
            "accounting_amount", "discrepancy", "count_date",
            "notes", "status", "resolution_notes",
            "resolved_by", "resolved_at",
        ]
        read_only_fields = [
            "id", "discrepancy", "count_date", "status",
            "resolved_at", "resolved_by", "accounting_amount", "group",
        ]
