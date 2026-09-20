from django.db import models

class Conversation(models.Model):
    participants = models.ManyToManyField(
        'users.CustomUser',
        related_name='conversations',
        verbose_name='参与人'
    )
    subject = models.CharField('主题', max_length=200, blank=True)
    related_application = models.ForeignKey(
        'applications.ApplicationProject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name='关联申请项目'
    )
    last_message_at = models.DateTimeField('最后消息时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        verbose_name = '对话'
        verbose_name_plural = '对话'
    
    def __str__(self):
        return f"对话 #{self.id} - {self.subject or '无主题'}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='所属对话'
    )
    sender = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='发送人'
    )
    content = models.TextField('消息内容')
    is_read = models.BooleanField('是否已读', default=False)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['conversation', 'created_at']
        verbose_name = '消息'
        verbose_name_plural = '消息'
    
    def __str__(self):
        return f"{self.sender.username} - {self.content[:50]}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.conversation.last_message_at = self.created_at
        self.conversation.save()

class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='所属消息'
    )
    file = models.FileField('附件', upload_to='message_attachments/')
    filename = models.CharField('文件名', max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = '消息附件'
        verbose_name_plural = '消息附件'
    
    def __str__(self):
        return self.filename
