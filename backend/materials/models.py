from django.db import models

class MaterialItem(models.Model):
    TYPE_TRANSCRIPT = 'transcript'
    TYPE_LANGUAGE = 'language'
    TYPE_CERTIFICATE = 'certificate'
    TYPE_ID = 'id'
    TYPE_FINANCIAL = 'financial'
    TYPE_OTHER = 'other'
    
    TYPE_CHOICES = [
        (TYPE_TRANSCRIPT, '成绩单'),
        (TYPE_LANGUAGE, '语言成绩'),
        (TYPE_CERTIFICATE, '在读证明/学位证'),
        (TYPE_ID, '身份证明'),
        (TYPE_FINANCIAL, '财力证明'),
        (TYPE_OTHER, '其他'),
    ]
    
    application = models.ForeignKey(
        'applications.ApplicationProject',
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='所属申请项目'
    )
    name = models.CharField('材料名称', max_length=200)
    material_type = models.CharField('材料类型', max_length=20, choices=TYPE_CHOICES, default=TYPE_OTHER)
    description = models.TextField('材料说明', blank=True)
    is_required = models.BooleanField('是否必需', default=True)
    is_completed = models.BooleanField('是否已完成', default=False)
    file = models.FileField('上传文件', upload_to='materials/', blank=True, null=True)
    uploaded_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_materials',
        verbose_name='上传人'
    )
    uploaded_at = models.DateTimeField('上传时间', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['application', '-is_required', 'material_type', 'name']
        verbose_name = '申请材料'
        verbose_name_plural = '申请材料'
    
    def __str__(self):
        return f"{self.application} - {self.name}"

class MaterialTemplate(models.Model):
    material_type = models.CharField('材料类型', max_length=20, choices=MaterialItem.TYPE_CHOICES)
    name = models.CharField('材料名称', max_length=200)
    description = models.TextField('材料说明', blank=True)
    is_required = models.BooleanField('是否必需', default=True)
    countries = models.CharField('适用国家', max_length=200, blank=True, help_text='多个国家用逗号分隔')
    degree_levels = models.CharField('适用学位', max_length=200, blank=True, help_text='bachelor,master,phd')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['material_type', 'name']
        verbose_name = '材料模板'
        verbose_name_plural = '材料模板'
    
    def __str__(self):
        return f"{self.get_material_type_display()} - {self.name}"
