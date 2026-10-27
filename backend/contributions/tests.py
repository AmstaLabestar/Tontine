from django.test import TestCase

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from groups.models import TontineGroup, GroupMembership
from members.models import Member
from contributions.models import Contribution

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", display_name="Test User"
        )
        self.group = TontineGroup.objects.create(name="Test Group", created_by=self.user)
        GroupMembership.objects.create(
            group=self.group, user=self.user, role=GroupMembership.ROLE_ADMIN
        )
        self.member = Member.objects.create(
            group=self.group, display_name="Member One", added_by=self.user
        )
        self.client.force_authenticate(user=self.user)

class ContributionTests(BaseTestCase):
    def test_create_contribution(self):
        data = {
            "member": str(self.member.id),
            "amount": 5000,
            "idempotency_key": "test-key-1",
            "deposit_date": "2026-01-15",
            "comment": "First deposit",
        }
        response = self.client.post(
            f"/api/groups/{self.group.id}/contributions/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contribution.objects.count(), 1)
        contrib = Contribution.objects.first()
        self.assertEqual(contrib.amount, 5000)

    def test_idempotency_prevents_duplicate(self):
        data = {
            "member": str(self.member.id),
            "amount": 5000,
            "idempotency_key": "dup-key-1",
        }
        self.client.post(f"/api/groups/{self.group.id}/contributions/", data, format="json")
        self.client.post(f"/api/groups/{self.group.id}/contributions/", data, format="json")
        self.assertEqual(Contribution.objects.count(), 1)

    def test_negative_amount_rejected(self):
        data = {
            "member": str(self.member.id),
            "amount": -100,
            "idempotency_key": "neg-key-1",
        }
        response = self.client.post(f"/api/groups/{self.group.id}/contributions/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_transition(self):
        contrib = Contribution.objects.create(
            group=self.group,
            member=self.member,
            amount=1000,
            status=Contribution.STATUS_DRAFT,
            idempotency_key="draft-key-1",
            recorder=self.user,
        )
        self.assertTrue(contrib.can_transition_to(Contribution.STATUS_CANCELLED))
        self.assertFalse(contrib.can_transition_to(Contribution.STATUS_CONFIRMED))

    def test_correction(self):
        contrib = Contribution.objects.create(
            group=self.group,
            member=self.member,
            amount=5000,
            status=Contribution.STATUS_CONFIRMED,
            idempotency_key="corr-key-1",
            recorder=self.user,
        )
        data = {
            "correction_type": "amount_adjustment",
            "new_amount": 4500,
            "reason": "Counting error",
        }
        response = self.client.post(
            f"/api/groups/{self.group.id}/contributions/{contrib.id}/correct/",
            data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contrib.refresh_from_db()
        self.assertEqual(contrib.status, Contribution.STATUS_CORRECTED)

    def test_cumulative_calculation(self):
        for i in range(3):
            Contribution.objects.create(
                group=self.group,
                member=self.member,
                amount=1000 * (i + 1),
                status=Contribution.STATUS_CONFIRMED,
                idempotency_key=f"cum-key-{i}",
                recorder=self.user,
            )
        from django.db.models import Sum
        total = Contribution.objects.filter(
            member=self.member, status__in=["confirmed", "corrected"]
        ).aggregate(total=Sum("amount"))["total"]
        self.assertEqual(total, 1000 + 2000 + 3000)

    def test_vault_verification(self):
        Contribution.objects.create(
            group=self.group,
            member=self.member,
            amount=10000,
            status=Contribution.STATUS_CONFIRMED,
            idempotency_key="vault-key-1",
            recorder=self.user,
        )
        data = {
            "physical_amount": 9500,
            "notes": "Counted by hand",
        }
        response = self.client.post(
            f"/api/groups/{self.group.id}/vault/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["discrepancy"], -500)

