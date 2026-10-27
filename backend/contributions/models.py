import uuid

from django.db import models

from groups.models import TontineGroup
from members.models import Member


class Contribution(models.Model):
    """A contribution (deposit) made by a member to the tontine.

    Key principles:
    - Amounts are stored as integers in the smallest currency unit (XOF has no subunit,
      so amounts are in whole XOF).
    - deposit_date: the real date the money was handed over (may be unknown).
    - recorded_at: when the recorder entered it into the system.
    - server_timestamp: when the server accepted it (for sync ordering).
    - client_created_at: when the device created it (for offline tracking).
    - idempotency_key: unique key generated on device to prevent duplicates.
    """

    STATUS_DRAFT = "draft"
    STATUS_PENDING_SYNC = "pending_sync"
    STATUS_SYNCED = "synced"
    STATUS_PENDING_VERIFICATION = "pending_verification"
    STATUS_CONFIRMED = "confirmed"
    STATUS_DISPUTED = "disputed"
    STATUS_CORRECTED = "corrected"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING_SYNC, "Pending sync"),
        (STATUS_SYNCED, "Synced"),
        (STATUS_PENDING_VERIFICATION, "Pending verification"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_DISPUTED, "Disputed"),
        (STATUS_CORRECTED, "Corrected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    ALLOWED_TRANSITIONS = {
        STATUS_DRAFT: {STATUS_PENDING_SYNC, STATUS_CANCELLED},
        STATUS_PENDING_SYNC: {STATUS_SYNCED, STATUS_CANCELLED},
        STATUS_SYNCED: {STATUS_PENDING_VERIFICATION, STATUS_CONFIRMED, STATUS_DISPUTED, STATUS_CANCELLED},
        STATUS_PENDING_VERIFICATION: {STATUS_CONFIRMED, STATUS_DISPUTED, STATUS_CANCELLED},
        STATUS_CONFIRMED: {STATUS_DISPUTED, STATUS_CORRECTED, STATUS_CANCELLED},
        STATUS_DISPUTED: {STATUS_CONFIRMED, STATUS_CANCELLED, STATUS_CORRECTED},
        STATUS_CORRECTED: set(),
        STATUS_CANCELLED: set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(TontineGroup, on_delete=models.CASCADE, related_name="contributions")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="contributions")
    amount = models.PositiveBigIntegerField()
    deposit_date = models.DateField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorder = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="contributions_recorded"
    )
    verifier = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="contributions_verified",
    )
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    idempotency_key = models.CharField(max_length=64, unique=True)
    client_created_at = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True, default="")
    device_id = models.CharField(max_length=64, blank=True, default="")
    is_historical_import = models.BooleanField(default=False)
    imported_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="contributions_imported",
    )
    imported_at = models.DateTimeField(null=True, blank=True)
    corrected_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="corrections_of"
    )
    cancelled_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="cancellations_of"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contributions_contribution"
        verbose_name = "Contribution"
        verbose_name_plural = "Contributions"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["group", "member"]),
            models.Index(fields=["group", "status"]),
            models.Index(fields=["idempotency_key"]),
        ]

    def __str__(self):
        return f"{self.member} - {self.amount} XOF ({self.status})"

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])



class ContributionCorrection(models.Model):
    """A correction operation linked to an original contribution."""

    CORRECTION_AMOUNT = "amount_adjustment"
    CORRECTION_STATUS = "status_change"
    CORRECTION_CANCELLATION = "cancellation"
    CORRECTION_CHOICES = [
        (CORRECTION_AMOUNT, "Amount adjustment"),
        (CORRECTION_STATUS, "Status change"),
        (CORRECTION_CANCELLATION, "Cancellation"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original = models.ForeignKey(
        "Contribution", on_delete=models.CASCADE, related_name="corrections"
    )
    correction_type = models.CharField(max_length=24, choices=CORRECTION_CHOICES)
    new_amount = models.PositiveBigIntegerField(null=True, blank=True)
    reason = models.TextField()
    author = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="corrections_authored"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resulting_contribution = models.ForeignKey(
        "Contribution", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="correction_source",
    )

    class Meta:
        db_table = "contributions_correction"
        verbose_name = "Contribution Correction"
        verbose_name_plural = "Contribution Corrections"

    def __str__(self):
        return f"Correction of {self.original} by {self.author}"

