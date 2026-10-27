from rest_framework import serializers

from .models import Contribution, ContributionCorrection


class ContributionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.display_name", read_only=True)
    recorder_name = serializers.CharField(source="recorder.display_name", read_only=True)
    verifier_name = serializers.CharField(source="verifier.display_name", read_only=True)

    class Meta:
        model = Contribution
        fields = [
            "id", "group", "member", "member_name", "amount",
            "deposit_date", "recorded_at", "recorder", "recorder_name",
            "verifier", "verifier_name", "status", "idempotency_key",
            "client_created_at", "server_timestamp", "comment",
            "device_id", "is_historical_import", "imported_by",
            "imported_at", "corrected_by", "cancelled_by", "updated_at",
        ]
        read_only_fields = [
            "id", "recorded_at", "server_timestamp", "recorder", "group",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value

    def validate(self, attrs):
        # Ensure member belongs to group
        member = attrs.get("member")
        group = attrs.get("group")
        if member and group and member.group_id != group.id:
            raise serializers.ValidationError("Member does not belong to this group.")
        return attrs


class ContributionStatusTransitionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=Contribution.STATUS_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class ContributionCorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionCorrection
        fields = [
            "id", "original", "correction_type", "new_amount",
            "reason", "author", "created_at", "resulting_contribution",
        ]
        read_only_fields = ["id", "author", "created_at", "original"]
