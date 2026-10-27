import uuid

from django.db import models

from groups.models import TontineGroup


class VaultVerification(models.Model):
    """Physical cash verification (vault count).

    A responsible counts the physical money in the vault and records it.
    The system compares it to the accounting balance and records any discrepancy.
    Discrepancies are never silently erased.
    """

    STATUS_PENDING_REVIEW = "pending_review"
    STATUS_RECONCILED = "reconciled"
    STATUS_DISCREPANCY_OPEN = "discrepancy_open"
    STATUS_DISCREPANCY_RESOLVED = "discrepancy_resolved"
    STATUS_CHOICES = [
        (STATUS_PENDING_REVIEW, "Pending review"),
        (STATUS_RECONCILED, "Reconciled"),
        (STATUS_DISCREPANCY_OPEN, "Discrepancy open"),
        (STATUS_DISCREPANCY_RESOLVED, "Discrepancy resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(TontineGroup, on_delete=models.CASCADE, related_name="vault_verifications")
    counted_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="vault_counts"
    )
    verified_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vault_verifications_second",
    )
    physical_amount = models.PositiveBigIntegerField()  # amount physically counted
    accounting_amount = models.PositiveBigIntegerField()  # system balance at count time
    discrepancy = models.BigIntegerField(default=0)  # physical - accounting
    count_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING_REVIEW)
    resolution_notes = models.TextField(blank=True, default="")
    resolved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vault_resolutions",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vault_verification"
        verbose_name = "Vault Verification"
        verbose_name_plural = "Vault Verifications"
        ordering = ["-count_date"]

    def __str__(self):
        return f"Vault count {self.physical_amount} vs {self.accounting_amount} ({self.status})"

    def save(self, *args, **kwargs):
        self.discrepancy = int(self.physical_amount) - int(self.accounting_amount)
        if self.discrepancy == 0:
            self.status = self.STATUS_RECONCILED
        elif self.status == self.STATUS_PENDING_REVIEW:
            self.status = self.STATUS_DISCREPANCY_OPEN
        super().save(*args, **kwargs)

