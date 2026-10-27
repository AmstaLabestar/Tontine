from rest_framework import generics, permissions

from .models import TontineGroup, GroupMembership
from .serializers import TontineGroupSerializer, GroupMembershipSerializer
from audit.models import AuditEvent
from audit.utils import log_audit_event


class TontineGroupListCreateView(generics.ListCreateAPIView):
    serializer_class = TontineGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TontineGroup.objects.filter(
            memberships__user=self.request.user, memberships__status="active"
        ).distinct()

    def perform_create(self, serializer):
        group = serializer.save(created_by=self.request.user)
        GroupMembership.objects.create(
            group=group, user=self.request.user, role=GroupMembership.ROLE_ADMIN
        )
        log_audit_event(
            group=group,
            event_type=AuditEvent.EVENT_GROUP_SETTINGS_CHANGED,
            actor=self.request.user,
            description=f"Group '{group.name}' created",
        )


class TontineGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TontineGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TontineGroup.objects.filter(
            memberships__user=self.request.user, memberships__status="active"
        ).distinct()


class GroupMembershipListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        return GroupMembership.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        group_id = self.kwargs.get("group_id")
        group = TontineGroup.objects.get(id=group_id)
        membership = serializer.save(group=group)
        log_audit_event(
            group=group,
            event_type=AuditEvent.EVENT_MEMBER_ADDED,
            actor=self.request.user,
            target_type="GroupMembership",
            target_id=str(membership.id),
            description=f"Member {membership.user} added to group",
        )


class GroupMembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        return GroupMembership.objects.filter(group_id=group_id)

