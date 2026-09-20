from django.contrib import admin

from .models import SubmissionSnapshot, SubmissionSnapshotMaterial


class SubmissionSnapshotMaterialInline(admin.TabularInline):
    model = SubmissionSnapshotMaterial
    extra = 0
    can_delete = False
    readonly_fields = [
        'material', 'name', 'material_type', 'material_type_display',
        'description', 'is_required', 'is_completed', 'file_name', 'file_url',
        'uploaded_by_name', 'uploaded_at',
    ]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SubmissionSnapshot)
class SubmissionSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'application', 'submitted_by', 'submitted_at',
        'application_round_name', 'ps_title', 'ps_version_number',
        'is_active_display', 'rolled_back_by', 'rolled_back_at',
    ]
    list_filter = ['rolled_back_at']
    readonly_fields = [
        'application', 'from_status', 'to_status',
        'ps_document', 'ps_version', 'ps_title', 'ps_version_number',
        'ps_content', 'ps_word_count',
        'application_round', 'application_round_name', 'application_round_deadline',
        'submitted_by', 'submitted_at',
        'rolled_back_at', 'rolled_back_by', 'rollback_reason', 'restored_status',
        'created_at',
    ]
    inlines = [SubmissionSnapshotMaterialInline]

    @admin.display(description='状态', boolean=True)
    def is_active_display(self, obj):
        return obj.is_active

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # 快照只通过业务接口回退，不从后台删除
        return False


admin.site.register(SubmissionSnapshotMaterial)
