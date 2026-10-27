import uuid

from django.db import models

from groups.models import TontineGroup


class Device(models.Model):
    """A registered device (phone) for a user in a group."""

    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_REVOKED, "Revoked"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(max_length=64, unique=True)  # client-generated
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="devices")
    group = models.ForeignKey(TontineGroup, on_delete=models.CASCADE, related_name="devices")
    name = models.CharField(max_length=120, blank=True, default="")
    platform = models.CharField(max_length=32, blank=True, default="")  # android, ios
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_cursor = models.CharField(max_length=64, blank=True, default="")
    registered_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="devices_revoked",
    )

    class Meta:
        db_table = "sync_device"
        verbose_name = "Device"
        verbose_name_plural = "Devices"

    def __str__(self):
        return f"{self.name} ({self.device_id})"


class SyncOperation(models.Model):
    """Tracks a sync operation for idempotency and conflict detection."""

    STATUS_PENDING = "pending"
    STATUS_APPLIED = "applied"
    STATUS_CONFLICT = "conflict"
    STATUS_DUPLICATE = "duplicate"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPLIED, "Applied"),
        (STATUS_CONFLICT, "Conflict"),
        (STATUS_DUPLICATE, "Duplicate"),
        (STATUS_REJECTED, "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=64, unique=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="sync_operations")
    group = models.ForeignKey(TontineGroup, on_delete=models.CASCADE, related_name="sync_operations")
    operation_type = models.CharField(max_length=32)  # create_contribution, update_status, etc.
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    conflict_reason = models.TextField(blank=True, default="")
    server_timestamp = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sync_operation"
        verbose_name = "Sync Operation"
        verbose_name_plural = "Sync Operations"
        ordering = ["-server_timestamp"]

    def __str__(self):
        return f"{self.operation_type} ({self.status})"


class SyncCursor(models.Model):
    """Tracks the last sync cursor for a device."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name="cursor")
    cursor = models.CharField(max_length=64, default="0")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sync_cursor"
        verbose_name = "Sync Cursor"
        verbose_name_plural = "Sync Cursors"

    def __str__(self):
        return f"{self.device} @ {self.cursor}"

