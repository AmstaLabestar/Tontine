from rest_framework import generics, permissions

from .models import Member
from .serializers import MemberSerializer
from audit.models import AuditEvent
from audit.utils import log_audit_event


class MemberListCreateView(generics.ListCreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        return Member.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        group_id = self.kwargs.get("group_id")
        from groups.models import TontineGroup
        group = TontineGroup.objects.get(id=group_id)
        member = serializer.save(group=group, added_by=self.request.user)
        log_audit_event(
            group=group,
            event_type=AuditEvent.EVENT_MEMBER_ADDED,
            actor=self.request.user,
            target_type="Member",
            target_id=str(member.id),
            description=f"Member '{member.display_name}' added",
        )


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get("group_id")
        return Member.objects.filter(group_id=group_id)

