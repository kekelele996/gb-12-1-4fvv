from django.db import models

class University(models.Model):
    name = models.CharField('院校名称', max_length=200)
    country = models.CharField('国家', max_length=100)
    city = models.CharField('城市', max_length=100)
    qs_ranking = models.IntegerField('QS排名', null=True, blank=True)
    times_ranking = models.IntegerField('Times排名', null=True, blank=True)
    description = models.TextField('院校简介', blank=True)
    logo = models.ImageField('校徽', upload_to='universities/logos/', blank=True, null=True)
    website = models.URLField('官网', max_length=500, blank=True)
    tuition_min = models.DecimalField('最低学费', max_digits=12, decimal_places=2, null=True, blank=True)
    tuition_max = models.DecimalField('最高学费', max_digits=12, decimal_places=2, null=True, blank=True)
    tuition_currency = models.CharField('学费货币', max_length=10, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['qs_ranking', 'name']
        verbose_name = '院校'
        verbose_name_plural = '院校'
    
    def __str__(self):
        return self.name

class Program(models.Model):
    DEGREE_CHOICES = [
        ('bachelor', '本科'),
        ('master', '硕士'),
        ('phd', '博士'),
    ]
    
    university = models.ForeignKey(
        University, 
        on_delete=models.CASCADE, 
        related_name='programs',
        verbose_name='所属院校'
    )
    name = models.CharField('专业名称', max_length=200)
    degree_level = models.CharField('学位层次', max_length=20, choices=DEGREE_CHOICES)
    department = models.CharField('院系', max_length=200, blank=True)
    description = models.TextField('专业简介', blank=True)
    duration_years = models.DecimalField('学制(年)', max_digits=3, decimal_places=1, null=True, blank=True)
    tuition = models.DecimalField('学费', max_digits=12, decimal_places=2, null=True, blank=True)
    language_of_instruction = models.CharField('授课语言', max_length=50, default='英语')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['university', 'name']
        verbose_name = '专业'
        verbose_name_plural = '专业'
    
    def __str__(self):
        return f"{self.university.name} - {self.name}"

class ApplicationRequirement(models.Model):
    program = models.OneToOneField(
        Program, 
        on_delete=models.CASCADE, 
        related_name='requirements',
        verbose_name='所属专业'
    )
    min_gpa = models.DecimalField('最低GPA要求', max_digits=3, decimal_places=2, null=True, blank=True)
    min_ielts = models.DecimalField('最低雅思要求', max_digits=3, decimal_places=1, null=True, blank=True)
    min_toefl = models.IntegerField('最低托福要求', null=True, blank=True)
    min_gre = models.IntegerField('最低GRE要求', null=True, blank=True)
    min_gmat = models.IntegerField('最低GMAT要求', null=True, blank=True)
    work_experience_required = models.BooleanField('需要工作经验', default=False)
    work_experience_years = models.IntegerField('要求工作年限', null=True, blank=True)
    other_requirements = models.TextField('其他要求', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '申请要求'
        verbose_name_plural = '申请要求'
    
    def __str__(self):
        return f"{self.program.name}的申请要求"

class ApplicationDeadline(models.Model):
    ROUND_CHOICES = [
        ('early_action', '提前申请'),
        ('early_decision', '提前决定'),
        ('round_1', '第一轮'),
        ('round_2', '第二轮'),
        ('round_3', '第三轮'),
        ('regular', '常规申请'),
    ]
    
    program = models.ForeignKey(
        Program, 
        on_delete=models.CASCADE, 
        related_name='deadlines',
        verbose_name='所属专业'
    )
    round_name = models.CharField('申请轮次', max_length=50, choices=ROUND_CHOICES)
    deadline_date = models.DateField('截止日期')
    decision_release_date = models.DateField('结果公布日期', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['program', 'deadline_date']
        verbose_name = '申请截止日期'
        verbose_name_plural = '申请截止日期'
    
    def __str__(self):
        return f"{self.program.name} - {self.get_round_name_display()}"

class UniversityRecommendation(models.Model):
    consultant = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name='顾问'
    )
    student = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='recommendations_received',
        verbose_name='学生'
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        verbose_name='推荐院校'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        verbose_name='推荐专业',
        null=True,
        blank=True
    )
    reason = models.TextField('推荐理由')
    match_score = models.IntegerField('匹配度评分', null=True, blank=True, help_text='1-100分')
    is_viewed = models.BooleanField('是否已查看', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '院校推荐'
        verbose_name_plural = '院校推荐'
    
    def __str__(self):
        return f"{self.consultant.username} 推荐 {self.university.name} 给 {self.student.username}"
