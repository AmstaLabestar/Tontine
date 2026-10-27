import uuid

from django.db import models

from groups.models import TontineGroup


class Member(models.Model):
    """A member of a tontine group.

    A Member represents a person who contributes to the tontine.
    They may or may not have a user account (for those without phones).
    """

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(TontineGroup, on_delete=models.CASCADE, related_name="members")
    display_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Optional link to a user account
    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="member_profiles",
    )
    # Track who added this member
    added_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="members_added"
    )

    class Meta:
        db_table = "members_member"
        verbose_name = "Member"
        verbose_name_plural = "Members"
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

