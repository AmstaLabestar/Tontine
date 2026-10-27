from django.urls import path
from .views import (
    ContributionListCreateView, ContributionDetailView,
    ContributionStatusTransitionView, ContributionCorrectionView,
)

urlpatterns = [
    path("", ContributionListCreateView.as_view(), name="contribution-list"),
    path("<uuid:pk>/", ContributionDetailView.as_view(), name="contribution-detail"),
    path("<uuid:pk>/transition/", ContributionStatusTransitionView.as_view(), name="contribution-transition"),
    path("<uuid:pk>/correct/", ContributionCorrectionView.as_view(), name="contribution-correct"),
]
