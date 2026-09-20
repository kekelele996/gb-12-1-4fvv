from django.db import models

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
