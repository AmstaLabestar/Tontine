import uuid

from django.db import models

from groups.models import TontineGroup


class AuditEvent(models.Model):
    """Immutable audit log entry.

    Every significant action is recorded here. Audit events cannot be
    modified or deleted through normal application flows.
    """

    EVENT_CONTRIBUTION_CREATED = "contribution_created"
    EVENT_CONTRIBUTION_VALIDATED = "contribution_validated"
    EVENT_CONTRIBUTION_DISPUTED = "contribution_disputed"
    EVENT_CONTRIBUTION_CORRECTED = "contribution_corrected"
    EVENT_CONTRIBUTION_CANCELLED = "contribution_cancelled"
    EVENT_MEMBER_ADDED = "member_added"
    EVENT_MEMBER_DEACTIVATED = "member_deactivated"
    EVENT_ROLE_CHANGED = "role_changed"
    EVENT_GROUP_SETTINGS_CHANGED = "group_settings_changed"
    EVENT_VAULT_VERIFIED = "vault_verified"
    EVENT_UNAUTHORIZED_ACCESS = "unauthorized_access"
    EVENT_SYNC_COMPLETED = "sync_completed"
    EVENT_DEVICE_REVOKED = "device_revoked"
    EVENT_HISTORICAL_IMPORT = "historical_import"

    EVENT_CHOICES = [
        (EVENT_CONTRIBUTION_CREATED, "Contribution created"),
        (EVENT_CONTRIBUTION_VALIDATED, "Contribution validated"),
        (EVENT_CONTRIBUTION_DISPUTED, "Contribution disputed"),
        (EVENT_CONTRIBUTION_CORRECTED, "Contribution corrected"),
        (EVENT_CONTRIBUTION_CANCELLED, "Contribution cancelled"),
        (EVENT_MEMBER_ADDED, "Member added"),
        (EVENT_MEMBER_DEACTIVATED, "Member deactivated"),
        (EVENT_ROLE_CHANGED, "Role changed"),
        (EVENT_GROUP_SETTINGS_CHANGED, "Group settings changed"),
        (EVENT_VAULT_VERIFIED, "Vault verified"),
        (EVENT_UNAUTHORIZED_ACCESS, "Unauthorized access attempt"),
        (EVENT_SYNC_COMPLETED, "Sync completed"),
        (EVENT_DEVICE_REVOKED, "Device revoked"),
        (EVENT_HISTORICAL_IMPORT, "Historical import"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(TontineGroup, on_delete=models.CASCADE, related_name="audit_events")
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="audit_events"
    )
    target_type = models.CharField(max_length=64, blank=True, default="")
    target_id = models.CharField(max_length=64, blank=True, default="")
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_event"
        verbose_name = "Audit Event"
        verbose_name_plural = "Audit Events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["group", "event_type"]),
            models.Index(fields=["group", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} by {self.actor} at {self.created_at}"

    def save(self, *args, **kwargs):
        # Audit events are append-only; updates are not allowed
        if self.pk and AuditEvent.objects.filter(pk=self.pk).exists():
            raise PermissionError("Audit events cannot be modified")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit events cannot be deleted")

