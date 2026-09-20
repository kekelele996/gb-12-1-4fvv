from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from .models import ApplicationProject, StatusChangeHistory, SubmissionSnapshot
from .serializers import (
    ApplicationProjectSerializer, ApplicationProjectListSerializer,
    StatusChangeHistorySerializer, SubmissionSnapshotSerializer
)


def get_submission_blockers(application):
    """递交阻塞项：必交材料未完成、个人陈述当前版本有未解决批注、申请批次已截止。"""
    blockers = []

    # 1. 必交材料须全部完成
    incomplete_materials = application.materials.filter(is_required=True, is_completed=False)
    for material in incomplete_materials:
        blockers.append({
            'type': 'material',
            'message': f'必交材料「{material.name}」未完成'
        })

    # 2. 个人陈述当前版本须无未解决批注
    ps_document = application.documents.filter(document_type='ps').first()
    if not ps_document or not ps_document.current_version:
        blockers.append({
            'type': 'ps',
            'message': '个人陈述（PS）尚未创建版本，无法固化版本快照'
        })
    else:
        current_version = ps_document.current_version
        unresolved_count = ps_document.comments.filter(
            version=current_version, is_resolved=False
        ).count()
        if unresolved_count:
            blockers.append({
                'type': 'ps',
                'message': f'个人陈述当前版本（v{current_version.version_number}）'
                           f'还有 {unresolved_count} 条未解决批注'
            })

    # 3. 申请批次须未截止
    if not application.application_round:
        blockers.append({
            'type': 'round',
            'message': '未选择申请批次'
        })
    elif application.application_round.deadline_date < timezone.localdate():
        round_name = application.application_round.get_round_name_display()
        deadline = application.application_round.deadline_date.strftime('%Y-%m-%d')
        blockers.append({
            'type': 'round',
            'message': f'申请批次「{round_name}」已于 {deadline} 截止'
        })

    return blockers


def build_materials_snapshot(application):
    """固化当前材料清单为快照数据（此后新增或修改材料不影响快照）。"""
    snapshot = []
    for material in application.materials.all():
        snapshot.append({
            'id': material.id,
            'name': material.name,
            'material_type': material.material_type,
            'material_type_display': material.get_material_type_display(),
            'description': material.description,
            'is_required': material.is_required,
            'is_completed': material.is_completed,
            'file': material.file.name if material.file else None,
            'uploaded_by': material.uploaded_by.username if material.uploaded_by else None,
            'uploaded_at': material.uploaded_at.isoformat() if material.uploaded_at else None,
            'notes': material.notes,
        })
    return snapshot


class ApplicationProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return ApplicationProject.objects.filter(student=user)
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            return ApplicationProject.objects.filter(student__in=students)
        return ApplicationProject.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationProjectListSerializer
        return ApplicationProjectSerializer

    @transaction.atomic
    def perform_update(self, serializer):
        instance = self.get_object()

        # 递交锁定后，申请批次不能移除或更换
        if instance.submission_locked and 'application_round' in serializer.validated_data:
            new_round = serializer.validated_data['application_round']
            new_round_id = new_round.id if new_round else None
            if new_round_id != instance.application_round_id:
                raise ValidationError({
                    'application_round': '申请已递交锁定，申请批次不能移除或更换'
                })

        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)

        if old_status != new_status:
            StatusChangeHistory.objects.create(
                application=instance,
                from_status=old_status,
                to_status=new_status,
                changed_by=self.request.user
            )
        serializer.save()

    @action(detail=True, methods=['get'])
    def submission_check(self, request, pk=None):
        """递交预检：返回阻塞项列表，供申请页展示。"""
        application = self.get_object()
        active_snapshot = application.submission_snapshots.filter(
            status=SubmissionSnapshot.STATUS_ACTIVE
        ).first()
        if active_snapshot:
            return Response({
                'can_submit': False,
                'already_submitted': True,
                'blocking_items': [],
                'snapshot': SubmissionSnapshotSerializer(active_snapshot).data,
            })
        blockers = get_submission_blockers(application)
        return Response({
            'can_submit': not blockers,
            'already_submitted': False,
            'blocking_items': blockers,
            'snapshot': None,
        })

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """顾问递交申请：校验阻塞项，通过后一次转为已提交并固化快照。重复或并发递交只生成一个快照。"""
        user = request.user
        if user.role not in ('consultant', 'admin'):
            return Response(
                {'error': '只有顾问或管理员可以递交申请'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.get_object()  # 校验访问权限与存在性

        with transaction.atomic():
            application = ApplicationProject.objects.select_for_update().get(pk=pk)

            # 幂等：已存在生效快照时直接返回，重复或并发递交只生成一个快照
            active_snapshot = application.submission_snapshots.filter(
                status=SubmissionSnapshot.STATUS_ACTIVE
            ).first()
            if active_snapshot:
                return Response({
                    'detail': '申请已递交，返回已存在的快照',
                    'snapshot': SubmissionSnapshotSerializer(active_snapshot).data,
                    'application': ApplicationProjectSerializer(application).data,
                })

            blockers = get_submission_blockers(application)
            if blockers:
                return Response(
                    {'error': '存在阻塞项，无法递交', 'blocking_items': blockers},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ps_document = application.documents.filter(document_type='ps').first()
            ps_version = ps_document.current_version if ps_document else None
            application_round = application.application_round

            snapshot_no = (application.submission_snapshots.aggregate(
                Max('snapshot_no')
            )['snapshot_no__max'] or 0) + 1

            snapshot = SubmissionSnapshot.objects.create(
                application=application,
                snapshot_no=snapshot_no,
                previous_status=application.status,
                application_round=application_round,
                application_round_name=(
                    application_round.get_round_name_display() if application_round else ''
                ),
                application_round_deadline=(
                    application_round.deadline_date if application_round else None
                ),
                ps_document=ps_document,
                ps_version=ps_version,
                ps_document_title=ps_document.title if ps_document else '',
                ps_version_number=ps_version.version_number if ps_version else None,
                ps_content=ps_version.content if ps_version else '',
                ps_word_count=ps_version.word_count if ps_version else 0,
                ps_change_note=ps_version.change_note if ps_version else '',
                materials_snapshot=build_materials_snapshot(application),
                submitted_by=user,
                submitted_at=timezone.now(),
            )

            # 状态一次转为已提交并锁定
            old_status = application.status
            application.status = ApplicationProject.STATUS_SUBMITTED
            application.submitted_at = snapshot.submitted_at
            application.submission_locked = True
            application.current_snapshot = snapshot
            application.save()

            # 锁定当前材料，之后不能移除或更换
            application.materials.all().update(is_locked=True)

            StatusChangeHistory.objects.create(
                application=application,
                from_status=old_status,
                to_status=ApplicationProject.STATUS_SUBMITTED,
                changed_by=user,
                change_reason=f'递交申请，生成快照 #{snapshot.snapshot_no}'
            )

        return Response({
            'detail': '递交成功，申请已锁定并固化快照',
            'snapshot': SubmissionSnapshotSerializer(snapshot).data,
            'application': ApplicationProjectSerializer(application).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def rollback_submission(self, request, pk=None):
        """管理员回退递交：必须说明原因，解除锁定，旧快照保留可查。"""
        if request.user.role != 'admin':
            return Response(
                {'error': '只有管理员可以回退递交'},
                status=status.HTTP_403_FORBIDDEN
            )
        reason = (request.data.get('reason') or '').strip()
        if not reason:
            return Response(
                {'error': '回退必须说明原因'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.get_object()

        with transaction.atomic():
            application = ApplicationProject.objects.select_for_update().get(pk=pk)
            snapshot = application.submission_snapshots.filter(
                status=SubmissionSnapshot.STATUS_ACTIVE
            ).first()
            if not snapshot:
                return Response(
                    {'error': '当前没有生效中的递交快照，无需回退'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            now = timezone.now()
            snapshot.status = SubmissionSnapshot.STATUS_ROLLED_BACK
            snapshot.rolled_back_by = request.user
            snapshot.rolled_back_at = now
            snapshot.rollback_reason = reason
            snapshot.save()

            old_status = application.status
            application.status = snapshot.previous_status
            application.submitted_at = None
            application.submission_locked = False
            application.current_snapshot = None
            application.save()

            # 解除材料锁定
            application.materials.filter(is_locked=True).update(is_locked=False)

            StatusChangeHistory.objects.create(
                application=application,
                from_status=old_status,
                to_status=application.status,
                changed_by=request.user,
                change_reason=f'递交回退（快照 #{snapshot.snapshot_no}）：{reason}'
            )

        return Response({
            'detail': f'已回退递交，状态恢复为「{application.get_status_display()}」',
            'snapshot': SubmissionSnapshotSerializer(snapshot).data,
            'application': ApplicationProjectSerializer(application).data,
        })

    @action(detail=True, methods=['get'])
    def snapshots(self, request, pk=None):
        """全部递交快照（含已回退的旧快照）。"""
        application = self.get_object()
        snapshots = application.submission_snapshots.all()
        return Response(SubmissionSnapshotSerializer(snapshots, many=True).data)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        application = self.get_object()
        old_status = application.status
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')

        if new_status not in [choice[0] for choice in ApplicationProject.STATUS_CHOICES]:
            return Response({'error': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)

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
