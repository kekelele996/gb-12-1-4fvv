from django.conf import settings
from django.db import models

from applications.models import ApplicationProject


class SubmissionSnapshot(models.Model):
    """申请递交快照：递交成功瞬间固化的材料清单与个人陈述版本。

    每次成功递交至多生成一个未回退（active）快照；并发/重复递交受
    applications + rolled_back_at__isnull 的唯一约束保护。
    """

    application = models.ForeignKey(
        'applications.ApplicationProject',
        on_delete=models.CASCADE,
        related_name='submission_snapshots',
        verbose_name='申请项目'
    )
    from_status = models.CharField(
        '递交前状态', max_length=20,
        choices=ApplicationProject.STATUS_CHOICES,
        blank=True
    )
    to_status = models.CharField(
        '递交后状态', max_length=20,
        choices=ApplicationProject.STATUS_CHOICES,
        default=ApplicationProject.STATUS_SUBMITTED
    )

    # —— 固化的个人陈述（PS）版本快照 ——
    ps_document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submission_snapshots',
        verbose_name='个人陈述文书'
    )
    ps_version = models.ForeignKey(
        'documents.DocumentVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submission_snapshots',
        verbose_name='个人陈述版本'
    )
    ps_title = models.CharField('个人陈述标题', max_length=200, blank=True)
    ps_version_number = models.IntegerField('个人陈述版本号', null=True, blank=True)
    ps_content = models.TextField('个人陈述正文快照', blank=True)
    ps_word_count = models.IntegerField('个人陈述字数', default=0)

    # —— 固化的申请批次快照 ——
    application_round = models.ForeignKey(
        'universities.ApplicationDeadline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submission_snapshots',
        verbose_name='申请批次'
    )
    application_round_name = models.CharField('申请批次名称', max_length=50, blank=True)
    application_round_deadline = models.DateField('申请批次截止日期', null=True, blank=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='递交人'
    )
    submitted_at = models.DateTimeField('递交时间', auto_now_add=True)

    # —— 管理员回退信息 ——
    rolled_back_at = models.DateTimeField('回退时间', null=True, blank=True)
    rolled_back_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rolled_back_submission_snapshots',
        verbose_name='回退操作人'
    )
    rollback_reason = models.TextField('回退原因', blank=True)
    restored_status = models.CharField(
        '回退后恢复状态', max_length=20,
        choices=ApplicationProject.STATUS_CHOICES,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '递交快照'
        verbose_name_plural = '递交快照'
        constraints = [
            models.UniqueConstraint(
                fields=['application'],
                condition=models.Q(rolled_back_at__isnull=True),
                name='unique_active_snapshot_per_application',
            ),
        ]

    def __str__(self):
        state = '生效中' if self.is_active else f'已回退({self.rolled_back_at:%Y-%m-%d})' if self.rolled_back_at else '已回退'
        return f"{self.application} 的递交快照 #{self.pk}（{state}）"

    @property
    def is_active(self):
        return self.rolled_back_at is None


class SubmissionSnapshotMaterial(models.Model):
    """递交时刻逐项固化的材料信息。快照行一旦生成即只读。"""

    snapshot = models.ForeignKey(
        SubmissionSnapshot,
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='所属递交快照'
    )
    material = models.ForeignKey(
        'materials.MaterialItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='snapshot_entries',
        verbose_name='来源材料'
    )
    name = models.CharField('材料名称', max_length=200)
    material_type = models.CharField('材料类型', max_length=20, blank=True)
    material_type_display = models.CharField('材料类型显示', max_length=50, blank=True)
    description = models.TextField('材料说明', blank=True)
    is_required = models.BooleanField('是否必需', default=True)
    is_completed = models.BooleanField('递交时是否已完成', default=False)
    file_name = models.CharField('递交时文件名', max_length=255, blank=True)
    file_url = models.CharField('递交时文件地址', max_length=500, blank=True)
    uploaded_by_name = models.CharField('上传人', max_length=150, blank=True)
    uploaded_at = models.DateTimeField('上传时间', null=True, blank=True)

    class Meta:
        ordering = ['snapshot', '-is_required', 'material_type', 'name']
        verbose_name = '递交快照材料'
        verbose_name_plural = '递交快照材料'

    def __str__(self):
        return f"快照 #{self.snapshot_id} - {self.name}"
