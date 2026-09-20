from django.db import models

class Document(models.Model):
    TYPE_PS = 'ps'
    TYPE_RL = 'rl'
    TYPE_CV = 'cv'
    TYPE_ESSAY = 'essay'
    TYPE_OTHER = 'other'
    
    TYPE_CHOICES = [
        (TYPE_PS, '个人陈述 (PS)'),
        (TYPE_RL, '推荐信 (RL)'),
        (TYPE_CV, '简历 (CV)'),
        (TYPE_ESSAY, 'Essay'),
        (TYPE_OTHER, '其他'),
    ]
    
    application = models.ForeignKey(
        'applications.ApplicationProject',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='所属申请项目'
    )
    document_type = models.CharField('文书类型', max_length=20, choices=TYPE_CHOICES)
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True)
    file = models.FileField('文件', upload_to='documents/', blank=True, null=True)
    current_version = models.ForeignKey(
        'DocumentVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_for',
        verbose_name='当前版本'
    )
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_documents',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '文书'
        verbose_name_plural = '文书'
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.title}"

class DocumentVersion(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='所属文书'
    )
    version_number = models.IntegerField('版本号')
    content = models.TextField('正文内容')
    file = models.FileField('文件附件', upload_to='document_versions/', blank=True, null=True)
    word_count = models.IntegerField('字数', default=0)
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='修改人'
    )
    change_note = models.TextField('修改说明', blank=True)
    diff_from_previous = models.TextField('与上一版本差异', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', '-version_number']
        verbose_name = '文书版本'
        verbose_name_plural = '文书版本'
        unique_together = ['document', 'version_number']
    
    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"
    
    def save(self, *args, **kwargs):
        if not self.version_number:
            max_version = self.document.versions.aggregate(
                models.Max('version_number')
            )['version_number__max'] or 0
            self.version_number = max_version + 1
        
        if not self.word_count and self.content:
            self.word_count = len(self.content)
        
        super().save(*args, **kwargs)

class DocumentComment(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='所属文书'
    )
    version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='版本',
        null=True,
        blank=True
    )
    author = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        verbose_name='评论人'
    )
    content = models.TextField('评论内容')
    start_position = models.IntegerField('起始位置', null=True, blank=True)
    end_position = models.IntegerField('结束位置', null=True, blank=True)
    highlighted_text = models.TextField('高亮文本', blank=True)
    is_resolved = models.BooleanField('是否已解决', default=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='父评论'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['document', 'created_at']
        verbose_name = '文书批注'
        verbose_name_plural = '文书批注'
    
    def __str__(self):
        return f"{self.author.username} - {self.document.title}"
