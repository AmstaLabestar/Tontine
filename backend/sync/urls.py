from django.urls import path
from .views import (
    DeviceRegisterView, DeviceListView, DeviceRevokeView,
    SyncPushView, SyncPullView, SyncStatusView,
)

urlpatterns = [
    path("devices/", DeviceRegisterView.as_view(), name="device-register"),
    path("devices/list/", DeviceListView.as_view(), name="device-list"),
    path("devices/<str:device_id>/revoke/", DeviceRevokeView.as_view(), name="device-revoke"),
    path("push/", SyncPushView.as_view(), name="sync-push"),
    path("pull/", SyncPullView.as_view(), name="sync-pull"),
    path("status/", SyncStatusView.as_view(), name="sync-status"),
]
