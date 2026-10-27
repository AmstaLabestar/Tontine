from rest_framework import generics, permissions

from .models import Contribution
from .serializers import ContributionSerializer


class ContributionListCreateView(generics.ListCreateAPIView):
    serializer_class = ContributionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        qs = Contribution.objects.filter(group_id=group_id)
        member_id = self.request.query_params.get("member")
        status_filter = self.request.query_params.get("status")
        if member_id:
            qs = qs.filter(member_id=member_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-recorded_at")

    def perform_create(self, serializer):
        from django.utils import timezone
        from groups.models import TontineGroup
        from audit.models import AuditEvent
        from audit.utils import log_audit_event

        group_id = self.kwargs.get("group_id")
        group = TontineGroup.objects.get(id=group_id)

        # Idempotency check
        idempotency_key = serializer.validated_data.get("idempotency_key")
        existing = Contribution.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            serializer.instance = existing
            return

        contribution = serializer.save(
            group=group,
            recorder=self.request.user,
            server_timestamp=timezone.now(),
        )

        if group.validation_policy == "dual":
            contribution.status = Contribution.STATUS_PENDING_VERIFICATION
        else:
            contribution.status = Contribution.STATUS_CONFIRMED
        contribution.save(update_fields=["status", "updated_at"])

        log_audit_event(
            group=group,
            event_type=AuditEvent.EVENT_CONTRIBUTION_CREATED,
            actor=self.request.user,
            target_type="Contribution",
            target_id=str(contribution.id),
            description=f"Contribution of {contribution.amount} XOF recorded for {contribution.member}",
            metadata={"idempotency_key": idempotency_key},
        )


class ContributionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContributionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        return Contribution.objects.filter(group_id=group_id)

    def perform_destroy(self, instance):
        raise PermissionError("Contributions cannot be deleted. Use cancellation.")



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import ContributionStatusTransitionSerializer, ContributionCorrectionSerializer
from .models import ContributionCorrection


class ContributionStatusTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id, pk):
        contribution = Contribution.objects.get(id=pk, group_id=group_id)
        serializer = ContributionStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["new_status"]
        reason = serializer.validated_data.get("reason", "")

        if not contribution.can_transition_to(new_status):
            return Response(
                {"error": f"Cannot transition from {contribution.status} to {new_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from audit.models import AuditEvent
        from audit.utils import log_audit_event

        old_status = contribution.status
        contribution.transition_to(new_status)

        if new_status == Contribution.STATUS_CONFIRMED:
            contribution.verifier = request.user
            contribution.save(update_fields=["verifier", "updated_at"])

        event_type = AuditEvent.EVENT_CONTRIBUTION_VALIDATED
        if new_status == Contribution.STATUS_DISPUTED:
            event_type = AuditEvent.EVENT_CONTRIBUTION_DISPUTED
        elif new_status == Contribution.STATUS_CANCELLED:
            event_type = AuditEvent.EVENT_CONTRIBUTION_CANCELLED
        elif new_status == Contribution.STATUS_CORRECTED:
            event_type = AuditEvent.EVENT_CONTRIBUTION_CORRECTED

        log_audit_event(
            group=contribution.group,
            event_type=event_type,
            actor=request.user,
            target_type="Contribution",
            target_id=str(contribution.id),
            description=f"Status changed from {old_status} to {new_status}. {reason}",
            metadata={"reason": reason},
        )

        from .serializers import ContributionSerializer
        return Response(ContributionSerializer(contribution).data)


class ContributionCorrectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id, pk):
        from django.utils import timezone

        original = Contribution.objects.get(id=pk, group_id=group_id)
        serializer = ContributionCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correction = serializer.save(
            original=original,
            author=request.user,
        )

        if correction.new_amount and correction.new_amount != original.amount:
            new_contribution = Contribution.objects.create(
                group=original.group,
                member=original.member,
                amount=correction.new_amount,
                deposit_date=original.deposit_date,
                recorder=request.user,
                status=Contribution.STATUS_CONFIRMED,
                idempotency_key=f"corr-{original.idempotency_key}",
                comment=f"Correction of {original.id}: {correction.reason}",
                is_historical_import=original.is_historical_import,
            )
            correction.resulting_contribution = new_contribution
            correction.save(update_fields=["resulting_contribution"])

            original.transition_to(Contribution.STATUS_CORRECTED)
            original.corrected_by = new_contribution
            original.save(update_fields=["corrected_by", "updated_at"])

        from audit.models import AuditEvent
        from audit.utils import log_audit_event
        log_audit_event(
            group=original.group,
            event_type=AuditEvent.EVENT_CONTRIBUTION_CORRECTED,
            actor=request.user,
            target_type="Contribution",
            target_id=str(original.id),
            description=f"Correction: {correction.reason}",
            metadata={
                "original_amount": original.amount,
                "new_amount": correction.new_amount,
                "correction_type": correction.correction_type,
            },
        )

        return Response(ContributionCorrectionSerializer(correction).data, status=status.HTTP_201_CREATED)
