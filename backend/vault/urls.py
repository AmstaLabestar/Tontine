from django.urls import path
from .views import VaultVerificationListCreateView, VaultVerificationResolveView

urlpatterns = [
    path("", VaultVerificationListCreateView.as_view(), name="vault-list"),
    path("<uuid:pk>/resolve/", VaultVerificationResolveView.as_view(), name="vault-resolve"),
]
