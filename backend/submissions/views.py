from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import SubmissionSnapshot
from .serializers import SubmissionSnapshotSerializer, SubmissionSnapshotListSerializer


class SubmissionSnapshotViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """只读的递交快照查询接口（旧快照始终可查，包括已回退的）。"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = SubmissionSnapshot.objects.select_related(
            'application', 'submitted_by', 'rolled_back_by'
        ).prefetch_related('materials')

        application_id = self.request.query_params.get('application')
        if application_id:
            queryset = queryset.filter(application_id=application_id)

        if user.role == 'student':
            queryset = queryset.filter(application__student=user)
        elif user.role == 'consultant':
            students = [sp.user_id for sp in user.students.all()]
            queryset = queryset.filter(application__student_id__in=students)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return SubmissionSnapshotListSerializer
        return SubmissionSnapshotSerializer
