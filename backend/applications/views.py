from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import ApplicationProject, StatusChangeHistory
from .serializers import (
    ApplicationProjectSerializer, ApplicationProjectListSerializer,
    StatusChangeHistorySerializer
)
from submissions.serializers import SubmissionSnapshotSerializer
from submissions.services import (
    SubmissionBlocked, evaluate_blockers, rollback_submission, submit_application,
)

# 已提交之后只允许向后流转的状态
_POST_SUBMIT_STATUSES = [
    ApplicationProject.STATUS_WAITING,
    ApplicationProject.STATUS_ADMITTED,
    ApplicationProject.STATUS_REJECTED,
    ApplicationProject.STATUS_WAITLISTED,
    ApplicationProject.STATUS_DEFERRED,
]


class ApplicationProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = ApplicationProject.objects.select_related(
            'student', 'university', 'program'
        ).prefetch_related(
            'status_history', 'submission_snapshots__materials'
        )
        if user.role == 'student':
            return queryset.filter(student=user)
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            return queryset.filter(student__in=students)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationProjectListSerializer
        return ApplicationProjectSerializer

    def _is_consultant_or_admin(self, user):
        return user.role in ('consultant', 'admin')

    def perform_destroy(self, instance):
        if instance.is_submission_locked or instance.submission_snapshots.exists():
            raise ValidationError({'detail': '申请已递交并锁定，不能删除；如需修改请由管理员回退递交。'})
        super().perform_destroy(instance)

    @transaction.atomic
    def perform_update(self, serializer):
        instance = self.get_object()
        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)
        new_round = serializer.validated_data.get(
            'application_round', instance.application_round
        )

        if new_status == ApplicationProject.STATUS_SUBMITTED:
            raise ValidationError(
                {'status': '不能直接标记为已提交，请使用“递交申请”接口完成校验与快照固化。'}
            )

        if instance.is_submission_locked:
            if new_round != instance.application_round:
                raise ValidationError(
                    {'application_round': '申请已递交并锁定，申请批次不能更换。'}
                )
            if new_status != old_status and new_status not in _POST_SUBMIT_STATUSES:
                raise ValidationError(
                    {'status': '申请已递交并锁定，如需回到递交前状态，请由管理员执行回退。'}
                )

        serializer.save()

        if old_status != new_status:
            StatusChangeHistory.objects.create(
                application=instance,
                from_status=old_status,
                to_status=new_status,
                changed_by=self.request.user
            )

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        application = self.get_object()
        old_status = application.status
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')

        if new_status not in [choice[0] for choice in ApplicationProject.STATUS_CHOICES]:
            return Response({'error': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)

        if new_status == ApplicationProject.STATUS_SUBMITTED:
            return Response(
                {'error': '不能直接标记为已提交，请使用“递交申请”接口完成校验与快照固化。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if application.is_submission_locked:
            if new_status == old_status:
                return Response(ApplicationProjectSerializer(application).data)
            if new_status not in _POST_SUBMIT_STATUSES:
                return Response(
                    {'error': '申请已递交并锁定，如需回到递交前状态，请由管理员执行回退。'},
                    status=status.HTTP_409_CONFLICT
                )

        application.status = new_status
        application.save()

        StatusChangeHistory.objects.create(
            application=application,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            change_reason=reason
        )

        return Response(ApplicationProjectSerializer(application).data)

    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        application = self.get_object()
        history = application.status_history.all()
        serializer = StatusChangeHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='submission/blockers')
    def submission_blockers(self, request, pk=None):
        """预检：列出当前递交阻塞项（空列表表示可以递交）。"""
        application = self.get_object()
        active = application.active_snapshot()
        data = {
            'is_submission_locked': application.is_submission_locked,
            'blocked': False,
            'blockers': [],
            'active_snapshot': SubmissionSnapshotSerializer(active).data if active else None,
        }
        if active is None:
            blockers = evaluate_blockers(application)
            data['blocked'] = bool(blockers)
            data['blockers'] = blockers
        return Response(data)

    @action(detail=True, methods=['post'], url_path='submission/submit')
    def submit(self, request, pk=None):
        """顾问/管理员递交：校验必交材料、PS 批注、申请批次；通过后原子锁定。"""
        application = self.get_object()

        if not self._is_consultant_or_admin(request.user):
            return Response(
                {'error': '只有顾问或管理员可以递交申请。'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            snapshot, created = submit_application(application, request.user)
        except SubmissionBlocked as exc:
            return Response(
                {
                    'detail': '递交被阻止，请先处理以下阻塞项。',
                    'blocked': True,
                    'blockers': exc.blockers,
                },
                status=status.HTTP_409_CONFLICT
            )

        application.refresh_from_db()
        return Response(
            {
                'detail': '申请递交成功' if created else '申请已处于已递交状态（重复递交未生成新快照）',
                'created': created,
                'application': ApplicationProjectSerializer(application).data,
                'snapshot': SubmissionSnapshotSerializer(snapshot).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='submission/rollback')
    def rollback(self, request, pk=None):
        """管理员说明原因回退递交；旧快照保留可查。"""
        application = self.get_object()

        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员可以回退递交。'},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get('reason', '')
        try:
            snapshot = rollback_submission(application, request.user, reason)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        application.refresh_from_db()
        return Response({
            'detail': '递交已回退，材料与申请批次已解锁。',
            'snapshot': SubmissionSnapshotSerializer(snapshot).data,
            'application': ApplicationProjectSerializer(application).data,
        })

    @action(detail=True, methods=['get'], url_path='submission/snapshots')
    def submission_snapshots(self, request, pk=None):
        """该申请的全部递交快照（含已回退的旧快照），按时间倒序。"""
        application = self.get_object()
        snapshots = application.submission_snapshots.all()
        serializer = SubmissionSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)
