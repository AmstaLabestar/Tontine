from rest_framework import serializers

from .models import TontineGroup, GroupMembership


class TontineGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TontineGroup
        fields = [
            "id", "name", "currency", "status", "validation_policy",
            "history_policy", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GroupMembershipSerializer(serializers.ModelSerializer):
    user_display = serializers.CharField(source="user.display_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GroupMembership
        fields = [
            "id", "group", "user", "user_display", "username",
            "role", "status", "joined_at", "updated_at",
        ]
        read_only_fields = ["id", "joined_at", "updated_at"]
