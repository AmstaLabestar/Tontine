from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import VaultVerification
from .serializers import VaultVerificationSerializer
from audit.models import AuditEvent
from audit.utils import log_audit_event


class VaultVerificationListCreateView(generics.ListCreateAPIView):
    serializer_class = VaultVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        return VaultVerification.objects.filter(group_id=group_id).order_by("-count_date")

    def perform_create(self, serializer):
        group_id = self.kwargs.get("group_id")
        from groups.models import TontineGroup
        from contributions.models import Contribution
        from django.db.models import Sum

        group = TontineGroup.objects.get(id=group_id)

        result = Contribution.objects.filter(
            group=group, status__in=["confirmed", "corrected"]
        ).aggregate(total=Sum("amount"))
        accounting_amount = result["total"] or 0

        verification = serializer.save(
            group=group,
            counted_by=self.request.user,
            accounting_amount=accounting_amount,
        )

        log_audit_event(
            group=group,
            event_type=AuditEvent.EVENT_VAULT_VERIFIED,
            actor=self.request.user,
            target_type="VaultVerification",
            target_id=str(verification.id),
            description=f"Vault count: physical={verification.physical_amount}, accounting={accounting_amount}, discrepancy={verification.discrepancy}",
            metadata={
                "physical_amount": verification.physical_amount,
                "accounting_amount": accounting_amount,
                "discrepancy": verification.discrepancy,
            },
        )


class VaultVerificationResolveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id, pk):
        verification = VaultVerification.objects.get(id=pk, group_id=group_id)
        notes = request.data.get("resolution_notes", "")
        verification.resolution_notes = notes
        verification.resolved_by = request.user
        verification.resolved_at = timezone.now()
        verification.status = VaultVerification.STATUS_DISCREPANCY_RESOLVED
        verification.save()

        log_audit_event(
            group=verification.group,
            event_type=AuditEvent.EVENT_VAULT_VERIFIED,
            actor=request.user,
            target_type="VaultVerification",
            target_id=str(verification.id),
            description=f"Discrepancy resolved: {notes}",
        )

        return Response(VaultVerificationSerializer(verification).data)

