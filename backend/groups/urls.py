from django.urls import path, include
from .views import (
    TontineGroupListCreateView, TontineGroupDetailView,
    GroupMembershipListCreateView, GroupMembershipDetailView,
)

urlpatterns = [
    path("", TontineGroupListCreateView.as_view(), name="group-list"),
    path("<uuid:pk>/", TontineGroupDetailView.as_view(), name="group-detail"),
    path("<uuid:group_id>/members/", GroupMembershipListCreateView.as_view(), name="member-list"),
    path("<uuid:group_id>/members/<uuid:pk>/", GroupMembershipDetailView.as_view(), name="member-detail"),
    path("<uuid:group_id>/tontine-members/", include("members.urls")),
    path("<uuid:group_id>/contributions/", include("contributions.urls")),
    path("<uuid:group_id>/audit/", include("audit.urls")),
    path("<uuid:group_id>/vault/", include("vault.urls")),
    path("<uuid:group_id>/sync/", include("sync.urls")),
]

