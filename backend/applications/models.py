from django.db import models
from django.utils import timezone

class ApplicationProject(models.Model):
    STATUS_PLANNING = 'planning'
    STATUS_PREPARING = 'preparing'
    STATUS_SUBMITTED = 'submitted'
    STATUS_WAITING = 'waiting'
    STATUS_ADMITTED = 'admitted'
    STATUS_REJECTED = 'rejected'
    STATUS_WAITLISTED = 'waitlisted'
    STATUS_DEFERRED = 'deferred'
    
    STATUS_CHOICES = [
        (STATUS_PLANNING, '规划中'),
        (STATUS_PREPARING, '准备材料'),
        (STATUS_SUBMITTED, '已提交'),
        (STATUS_WAITING, '等待结果'),
        (STATUS_ADMITTED, '已录取'),
        (STATUS_REJECTED, '已拒'),
        (STATUS_WAITLISTED, '候补'),
        (STATUS_DEFERRED, '延期'),
    ]
    
    student = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='学生'
    )
    university = models.ForeignKey(
        'universities.University',
        on_delete=models.CASCADE,
        verbose_name='目标院校'
    )
    program = models.ForeignKey(
        'universities.Program',
        on_delete=models.CASCADE,
        verbose_name='申请专业'
    )
    application_round = models.ForeignKey(
        'universities.ApplicationDeadline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='申请轮次'
    )
    status = models.CharField(
        '申请状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PLANNING
    )
    notes = models.TextField('备注', blank=True)
    application_fee = models.DecimalField('申请费', max_digits=10, decimal_places=2, null=True, blank=True)
    fee_paid = models.BooleanField('申请费已缴纳', default=False)
    submitted_at = models.DateTimeField('提交时间', null=True, blank=True)
    result_date = models.DateTimeField('结果公布时间', null=True, blank=True)
    submission_locked = models.BooleanField('递交锁定', default=False)
    current_snapshot = models.ForeignKey(
        'SubmissionSnapshot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_for',
        verbose_name='当前递交快照'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '申请项目'
        verbose_name_plural = '申请项目'
    
    def __str__(self):
        return f"{self.student.username} - {self.university.name} - {self.program.name}"
    
    def get_materials_progress(self):
        total = self.materials.count()
        if total == 0:
            return 0
        completed = self.materials.filter(is_completed=True).count()
        return int((completed / total) * 100)

class StatusChangeHistory(models.Model):
    application = models.ForeignKey(
        ApplicationProject,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='申请项目'
    )
    from_status = models.CharField('原状态', max_length=20, choices=ApplicationProject.STATUS_CHOICES, null=True, blank=True)
    to_status = models.CharField('新状态', max_length=20, choices=ApplicationProject.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='修改人'
    )
    change_reason = models.TextField('变更原因', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '状态变更记录'
        verbose_name_plural = '状态变更记录'
    
    def __str__(self):
        return f"{self.application} - {self.get_to_status_display()}"

class SubmissionSnapshot(models.Model):
    """递交快照：申请递交成功时固化材料清单与个人陈述版本，递交后不可变。"""
    STATUS_ACTIVE = 'active'
    STATUS_ROLLED_BACK = 'rolled_back'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, '生效中'),
        (STATUS_ROLLED_BACK, '已回退'),
    ]

    application = models.ForeignKey(
        ApplicationProject,
        on_delete=models.CASCADE,
        related_name='submission_snapshots',
        verbose_name='申请项目'
    )
    snapshot_no = models.PositiveIntegerField('快照序号')
    status = models.CharField(
        '快照状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    previous_status = models.CharField(
        '递交前状态',
        max_length=20,
        choices=ApplicationProject.STATUS_CHOICES,
        default=ApplicationProject.STATUS_PREPARING
    )
    # 固化申请批次信息
    application_round = models.ForeignKey(
        'universities.ApplicationDeadline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='申请批次'
    )
    application_round_name = models.CharField('申请批次名称', max_length=100, blank=True)
    application_round_deadline = models.DateField('批次截止日期', null=True, blank=True)
    # 固化个人陈述版本
    ps_document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='个人陈述文书'
    )
    ps_version = models.ForeignKey(
        'documents.DocumentVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='个人陈述版本'
    )
    ps_document_title = models.CharField('文书标题', max_length=200, blank=True)
    ps_version_number = models.IntegerField('版本号', null=True, blank=True)
    ps_content = models.TextField('版本正文快照', blank=True)
    ps_word_count = models.IntegerField('字数', default=0)
    ps_change_note = models.TextField('版本修改说明', blank=True)
    # 固化材料清单
    materials_snapshot = models.JSONField('材料快照', default=list)

    submitted_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='submission_snapshots',
        verbose_name='递交人'
    )
    submitted_at = models.DateTimeField('递交时间', default=timezone.now)
    rolled_back_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rolled_back_snapshots',
        verbose_name='回退操作人'
    )
    rolled_back_at = models.DateTimeField('回退时间', null=True, blank=True)
    rollback_reason = models.TextField('回退原因', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-snapshot_no']
        verbose_name = '递交快照'
        verbose_name_plural = '递交快照'
        unique_together = ['application', 'snapshot_no']
        constraints = [
            models.UniqueConstraint(
                fields=['application'],
                condition=models.Q(status='active'),
                name='unique_active_snapshot_per_application'
            )
        ]

    def __str__(self):
        return f"{self.application} - 快照#{self.snapshot_no}"
