"""申请递交锁定业务服务。

- evaluate_blockers：按规则校验递交前置条件并返回阻塞项
- submit_application：原子地完成「状态一次转为已提交 + 固化快照 + 锁定」
- rollback_submission：管理员填写原因后回退，保留旧快照可查

并发/重复递交依靠 select_for_update 行锁与
SubmissionSnapshot 的部分唯一约束共同保证只生成一个快照。
"""
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from applications.models import ApplicationProject, StatusChangeHistory
from documents.models import Document
from materials.models import MaterialItem
from .models import SubmissionSnapshot, SubmissionSnapshotMaterial


# —— 阻塞项类型 ——
BLOCKER_REQUIRED_MATERIAL = 'required_material_incomplete'
BLOCKER_PS_MISSING = 'ps_missing'
BLOCKER_PS_VERSION_MISSING = 'ps_version_missing'
BLOCKER_PS_UNRESOLVED_COMMENT = 'ps_unresolved_comment'
BLOCKER_ROUND_MISSING = 'application_round_missing'
BLOCKER_ROUND_CLOSED = 'application_round_closed'

BLOCKER_MESSAGES = {
    BLOCKER_REQUIRED_MATERIAL: '必交材料尚未完成',
    BLOCKER_PS_MISSING: '缺少个人陈述（PS）文书',
    BLOCKER_PS_VERSION_MISSING: '个人陈述尚无已保存版本',
    BLOCKER_PS_UNRESOLVED_COMMENT: '个人陈述当前版本存在未解决批注',
    BLOCKER_ROUND_MISSING: '未选择申请批次',
    BLOCKER_ROUND_CLOSED: '申请批次已截止',
}


class SubmissionBlocked(Exception):
    """递交前置条件不满足。blockers 为结构化阻塞项列表。"""

    def __init__(self, blockers):
        self.blockers = blockers
        super().__init__('; '.join(b['message'] for b in blockers))


def _blocker(code, message=None, **extra):
    item = {'code': code, 'message': message or BLOCKER_MESSAGES.get(code, code)}
    item.update(extra)
    return item


def evaluate_blockers(application):
    """返回递交阻塞项列表；空列表代表可以递交。

    规则：
    1. 所有必交材料（is_required=True）必须已完成（is_completed=True）；
    2. 个人陈述（PS）必须存在且当前版本已保存；
    3. 个人陈述当前版本无未解决批注；
    4. 申请批次已选择且截止日期未过。
    """
    blockers = []

    # 1. 必交材料
    incomplete_materials = list(
        application.materials.filter(is_required=True, is_completed=False)
    )
    if incomplete_materials:
        blockers.append(_blocker(
            BLOCKER_REQUIRED_MATERIAL,
            materials=[{
                'id': m.id,
                'name': m.name,
                'material_type': m.material_type,
            } for m in incomplete_materials],
        ))

    # 2/3. 个人陈述
    ps = (
        Document.objects
        .filter(application=application, document_type=Document.TYPE_PS)
        .select_related('current_version')
        .order_by('id')
        .first()
    )
    if ps is None:
        blockers.append(_blocker(BLOCKER_PS_MISSING))
    elif ps.current_version is None:
        blockers.append(_blocker(
            BLOCKER_PS_VERSION_MISSING,
            ps_document={'id': ps.id, 'title': ps.title},
        ))
    else:
        current_version = ps.current_version
        # 未解决批注：文档级批注（未绑定版本）或绑定在当前版本上的批注；
        # 绑定在历史版本上的批注不阻塞当前版本递交
        unresolved = ps.comments.filter(
            is_resolved=False
        ).filter(
            models.Q(version=current_version) | models.Q(version__isnull=True)
        )
        unresolved_count = unresolved.count()
        if unresolved_count > 0:
            blockers.append(_blocker(
                BLOCKER_PS_UNRESOLVED_COMMENT,
                ps_document={'id': ps.id, 'title': ps.title},
                ps_version={
                    'id': current_version.id,
                    'version_number': current_version.version_number,
                },
                unresolved_count=unresolved_count,
                comment_ids=list(unresolved.values_list('id', flat=True)),
            ))

    # 4. 申请批次
    round_obj = application.application_round
    if round_obj is None:
        blockers.append(_blocker(BLOCKER_ROUND_MISSING))
    elif round_obj.deadline_date is not None and \
            timezone.localdate() > round_obj.deadline_date:
        blockers.append(_blocker(
            BLOCKER_ROUND_CLOSED,
            application_round={
                'id': round_obj.id,
                'round_name': round_obj.round_name,
                'deadline_date': round_obj.deadline_date.isoformat(),
            },
        ))

    return blockers


def _snapshot_material_rows(snapshot, materials):
    rows = []
    for material in materials:
        file_obj = material.file
        rows.append(SubmissionSnapshotMaterial(
            snapshot=snapshot,
            material=material,
            name=material.name,
            material_type=material.material_type,
            material_type_display=material.get_material_type_display(),
            description=material.description,
            is_required=material.is_required,
            is_completed=material.is_completed,
            file_name=file_obj.name.split('/')[-1] if file_obj else '',
            file_url=file_obj.url if file_obj else '',
            uploaded_by_name=material.uploaded_by.username if material.uploaded_by else '',
            uploaded_at=material.uploaded_at,
        ))
    return rows


def submit_application(application, user):
    """执行递交。成功返回 (snapshot, created: bool)。

    - 已存在生效快照时直接返回旧快照（幂等，created=False），重复/并发递交
      不会产生第二个快照；
    - 前置条件不满足时抛出 SubmissionBlocked；
    - 并发竞争落败时返回对手已创建的快照。
    """
    with transaction.atomic():
        # 锁住行，串行化同一申请项目上的并发递交
        locked = ApplicationProject.objects.select_for_update().get(pk=application.pk)

        existing = SubmissionSnapshot.objects.filter(
            application=locked, rolled_back_at__isnull=True
        ).first()
        if existing is not None:
            return existing, False

        blockers = evaluate_blockers(locked)
        if blockers:
            raise SubmissionBlocked(blockers)

        ps = (
            Document.objects
            .filter(application=locked, document_type=Document.TYPE_PS)
            .select_related('current_version')
            .order_by('id')
            .first()
        )
        ps_version = ps.current_version if ps else None
        round_obj = locked.application_round

        from_status = locked.status
        snapshot = SubmissionSnapshot(
            application=locked,
            from_status=from_status,
            to_status=ApplicationProject.STATUS_SUBMITTED,
            ps_document=ps,
            ps_version=ps_version,
            ps_title=ps.title if ps else '',
            ps_version_number=ps_version.version_number if ps_version else None,
            ps_content=ps_version.content if ps_version else '',
            ps_word_count=ps_version.word_count if ps_version else 0,
            application_round=round_obj,
            application_round_name=round_obj.get_round_name_display() if round_obj else '',
            application_round_deadline=round_obj.deadline_date if round_obj else None,
            submitted_by=user,
        )
        try:
            # 嵌套保存点：极端并发下唯一约束报错时可安全回滚到保存点，
            # 不污染外层事务（PostgreSQL 约束冲突会中止整个事务）
            with transaction.atomic():
                snapshot.save()
        except IntegrityError:
            # 竞争事务已先行提交生效快照：返回它，保证只存在一个快照
            existing = SubmissionSnapshot.objects.filter(
                application=locked, rolled_back_at__isnull=True
            ).first()
            if existing is not None:
                return existing, False
            raise

        materials = list(locked.materials.all())
        SubmissionSnapshotMaterial.objects.bulk_create(
            _snapshot_material_rows(snapshot, materials)
        )
        # 锁定当前材料：此后不可移除/更换（见 materials 视图守卫）
        MaterialItem.objects.filter(
            application=locked, is_locked=False
        ).update(is_locked=True)

        locked.status = ApplicationProject.STATUS_SUBMITTED
        locked.is_submission_locked = True
        locked.submitted_at = timezone.now()
        locked.save(update_fields=[
            'status', 'is_submission_locked', 'submitted_at', 'updated_at'
        ])

        StatusChangeHistory.objects.create(
            application=locked,
            from_status=from_status,
            to_status=ApplicationProject.STATUS_SUBMITTED,
            changed_by=user,
            change_reason='顾问递交申请，已生成递交快照并固化材料与个人陈述版本',
        )
        return snapshot, True


def rollback_submission(application, user, reason):
    """管理员说明原因回退当前生效快照。成功返回快照；无生效快照抛 ValueError。"""
    reason = (reason or '').strip()
    if not reason:
        raise ValueError('回退必须填写原因')

    with transaction.atomic():
        locked = ApplicationProject.objects.select_for_update().get(pk=application.pk)
        snapshot = SubmissionSnapshot.objects.select_for_update().filter(
            application=locked, rolled_back_at__isnull=True
        ).first()
        if snapshot is None:
            raise ValueError('该申请没有生效中的递交快照，无法回退')

        restored_status = snapshot.from_status or ApplicationProject.STATUS_PREPARING
        now = timezone.now()

        snapshot.rolled_back_at = now
        snapshot.rolled_back_by = user
        snapshot.rollback_reason = reason
        snapshot.restored_status = restored_status
        snapshot.save(update_fields=[
            'rolled_back_at', 'rolled_back_by', 'rollback_reason',
            'restored_status',
        ])

        # 解除锁定：回退后材料/批次恢复可编辑（旧快照仍可查）
        previous_status = locked.status
        locked.status = restored_status
        locked.is_submission_locked = False
        locked.submitted_at = None
        locked.save(update_fields=[
            'status', 'is_submission_locked', 'submitted_at', 'updated_at'
        ])
        MaterialItem.objects.filter(application=locked).update(is_locked=False)

        StatusChangeHistory.objects.create(
            application=locked,
            from_status=previous_status,
            to_status=restored_status,
            changed_by=user,
            change_reason=f'管理员回退递交：{reason}',
        )
        return snapshot
