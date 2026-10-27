from rest_framework import generics, permissions

from .models import Device, SyncOperation, SyncCursor
from .serializers import DeviceSerializer


class DeviceRegisterView(generics.CreateAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        device = serializer.save(user=self.request.user)
        SyncCursor.objects.create(device=device)


class DeviceListView(generics.ListAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .serializers import SyncPushSerializer, SyncPullSerializer
from .models import SyncOperation
from contributions.models import Contribution
from members.models import Member
from audit.models import AuditEvent
from audit.utils import log_audit_event


class DeviceRevokeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, device_id):
        device = Device.objects.get(device_id=device_id)
        device.status = Device.STATUS_REVOKED
        device.revoked_at = timezone.now()
        device.revoked_by = request.user
        device.save()

        log_audit_event(
            group=device.group,
            event_type=AuditEvent.EVENT_DEVICE_REVOKED,
            actor=request.user,
            target_type="Device",
            target_id=str(device.id),
            description=f"Device {device.device_id} revoked",
        )
        return Response({"detail": "Device revoked."})


class SyncPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        serializer = SyncPushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        operations = serializer.validated_data["operations"]
        results = []

        for op in operations:
            idempotency_key = op.get("idempotency_key")
            if not idempotency_key:
                results.append({"status": "rejected", "reason": "Missing idempotency_key"})
                continue

            existing = SyncOperation.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                results.append({"status": "duplicate", "id": str(existing.id)})
                continue

            device_id = op.get("device_id")
            device = Device.objects.filter(device_id=device_id).first()
            if not device or device.status != Device.STATUS_ACTIVE:
                results.append({"status": "rejected", "reason": "Device not active"})
                continue

            sync_op = SyncOperation.objects.create(
                idempotency_key=idempotency_key,
                device=device,
                group_id=group_id,
                operation_type=op.get("operation_type", "unknown"),
                payload=op.get("payload", {}),
                status=SyncOperation.STATUS_PENDING,
            )

            op_type = op.get("operation_type")
            if op_type == "create_contribution":
                payload = op.get("payload", {})
                try:
                    contrib_key = payload.get("idempotency_key")
                    existing_contrib = Contribution.objects.filter(
                        idempotency_key=contrib_key
                    ).first()
                    if existing_contrib:
                        sync_op.status = SyncOperation.STATUS_DUPLICATE
                        sync_op.save()
                        results.append({"status": "duplicate", "contribution_id": str(existing_contrib.id)})
                        continue

                    member = Member.objects.get(id=payload["member_id"])
                    contribution = Contribution.objects.create(
                        group_id=group_id,
                        member=member,
                        amount=payload["amount"],
                        deposit_date=payload.get("deposit_date"),
                        recorder=request.user,
                        status=Contribution.STATUS_SYNCED,
                        idempotency_key=contrib_key,
                        client_created_at=payload.get("client_created_at"),
                        server_timestamp=timezone.now(),
                        comment=payload.get("comment", ""),
                        device_id=device_id,
                        is_historical_import=payload.get("is_historical_import", False),
                    )
                    sync_op.status = SyncOperation.STATUS_APPLIED
                    sync_op.save()
                    results.append({"status": "applied", "contribution_id": str(contribution.id)})
                except Exception as e:
                    sync_op.status = SyncOperation.STATUS_REJECTED
                    sync_op.conflict_reason = str(e)
                    sync_op.save()
                    results.append({"status": "rejected", "reason": str(e)})
            else:
                sync_op.status = SyncOperation.STATUS_APPLIED
                sync_op.save()
                results.append({"status": "applied", "operation_id": str(sync_op.id)})

        return Response({"results": results})



class SyncPullView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        serializer = SyncPullSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        limit = serializer.validated_data["limit"]

        contributions = Contribution.objects.filter(
            group_id=group_id,
        ).order_by("recorded_at")

        data = []
        for c in contributions[:limit]:
            data.append({
                "type": "contribution",
                "id": str(c.id),
                "member_id": str(c.member_id),
                "amount": c.amount,
                "status": c.status,
                "deposit_date": c.deposit_date.isoformat() if c.deposit_date else None,
                "recorded_at": c.recorded_at.isoformat(),
                "idempotency_key": c.idempotency_key,
            })

        new_cursor = str(len(data))

        return Response({
            "data": data,
            "cursor": new_cursor,
            "has_more": len(data) >= limit,
        })


class SyncStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        device_id = request.query_params.get("device_id")
        device = Device.objects.filter(device_id=device_id).first()

        pending_count = SyncOperation.objects.filter(
            group_id=group_id, status=SyncOperation.STATUS_PENDING
        ).count()

        return Response({
            "pending_operations": pending_count,
            "device_status": device.status if device else "unknown",
            "last_sync_at": device.last_sync_at.isoformat() if device and device.last_sync_at else None,
        })
