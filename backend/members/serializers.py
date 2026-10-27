from rest_framework import serializers

from .models import Member


class MemberSerializer(serializers.ModelSerializer):
    total_contributions = serializers.SerializerMethodField()
    contribution_count = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "id", "group", "display_name", "phone", "status",
            "joined_at", "updated_at", "user", "added_by",
            "total_contributions", "contribution_count",
        ]
        read_only_fields = ["id", "joined_at", "updated_at"]

    def get_total_contributions(self, obj):
        from django.db.models import Sum
        from contributions.models import Contribution
        result = Contribution.objects.filter(
            member=obj, status__in=["confirmed", "corrected"]
        ).aggregate(total=Sum("amount"))
        return result["total"] or 0

    def get_contribution_count(self, obj):
        from contributions.models import Contribution
        return Contribution.objects.filter(
            member=obj, status__in=["confirmed", "corrected"]
        ).count()
