import uuid

from django.db import models

from accounts.models import User


class TontineGroup(models.Model):
    """A tontine group: a collection of people who save together."""

    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_CLOSED, "Closed"),
    ]

    VALIDATION_SINGLE = "single"
    VALIDATION_DUAL = "dual"
    VALIDATION_CHOICES = [
        (VALIDATION_SINGLE, "Single validation"),
        (VALIDATION_DUAL, "Dual validation (recorder + verifier)"),
    ]

    HISTORY_ALL_MEMBERS = "all_members"
    HISTORY_ADMINS_ONLY = "admins_only"
    HISTORY_CHOICES = [
        (HISTORY_ALL_MEMBERS, "All members can view history"),
        (HISTORY_ADMINS_ONLY, "Only admins can view history"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    currency = models.CharField(max_length=8, default="XOF")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    validation_policy = models.CharField(
        max_length=16, choices=VALIDATION_CHOICES, default=VALIDATION_SINGLE
    )
    history_policy = models.CharField(
        max_length=20, choices=HISTORY_CHOICES, default=HISTORY_ALL_MEMBERS
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="groups_created"
    )

    class Meta:
        db_table = "groups_tontine_group"
        verbose_name = "Tontine Group"
        verbose_name_plural = "Tontine Groups"

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    """Links a user to a tontine group with a role."""

    ROLE_ADMIN = "admin"
    ROLE_RECORDER = "recorder"
    ROLE_MEMBER = "member"
    ROLE_AUDITOR = "auditor"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_RECORDER, "Recorder"),
        (ROLE_MEMBER, "Member"),
        (ROLE_AUDITOR, "Auditor"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(TontineGroup, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "groups_membership"
        unique_together = [("group", "user")]
        verbose_name = "Group Membership"
        verbose_name_plural = "Group Memberships"

    def __str__(self):
        return f"{self.user} in {self.group} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def can_record(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_RECORDER)

    @property
    def can_verify(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_AUDITOR)

    @property
    def can_manage_members(self):
        return self.role == self.ROLE_ADMIN

