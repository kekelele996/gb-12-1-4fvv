from django.db import models

class TimelineEvent(models.Model):
    TYPE_EXAM = 'exam'
    TYPE_DOCUMENT = 'document'
    TYPE_APPLICATION = 'application'
    TYPE_INTERVIEW = 'interview'
    TYPE_DECISION = 'decision'
    TYPE_CUSTOM = 'custom'
    
    TYPE_CHOICES = [
        (TYPE_EXAM, '语言考试'),
        (TYPE_DOCUMENT, '文书截止'),
        (TYPE_APPLICATION, '网申截止'),
        (TYPE_INTERVIEW, '面试'),
        (TYPE_DECISION, '预计出结果'),
        (TYPE_CUSTOM, '自定义'),
    ]
    
    application = models.ForeignKey(
        'applications.ApplicationProject',
        on_delete=models.CASCADE,
        related_name='timeline_events',
        verbose_name='所属申请项目'
    )
    event_type = models.CharField('事件类型', max_length=20, choices=TYPE_CHOICES)
    title = models.CharField('事件标题', max_length=200)
    description = models.TextField('事件描述', blank=True)
    event_date = models.DateTimeField('事件日期')
    deadline_date = models.DateTimeField('截止日期', null=True, blank=True)
    reminder_sent = models.BooleanField('提醒已发送', default=False)
    is_completed = models.BooleanField('是否完成', default=False)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_timeline_events',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['application', 'event_date']
        verbose_name = '时间线事件'
        verbose_name_plural = '时间线事件'
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.title}"

class Notification(models.Model):
    TYPE_EMAIL = 'email'
    TYPE_SYSTEM = 'system'
    TYPE_SMS = 'sms'
    
    TYPE_CHOICES = [
        (TYPE_EMAIL, '邮件'),
        (TYPE_SYSTEM, '站内消息'),
        (TYPE_SMS, '短信'),
    ]
    
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, '低'),
        (PRIORITY_MEDIUM, '中'),
        (PRIORITY_HIGH, '高'),
    ]
    
    recipient = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='接收人'
    )
    notification_type = models.CharField('通知类型', max_length=20, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    related_event = models.ForeignKey(
        TimelineEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='关联事件'
    )
    related_application = models.ForeignKey(
        'applications.ApplicationProject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='关联申请'
    )
    is_read = models.BooleanField('是否已读', default=False)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)
    sent_at = models.DateTimeField('发送时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '通知'
        verbose_name_plural = '通知'
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
