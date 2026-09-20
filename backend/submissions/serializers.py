from rest_framework import serializers

from .models import SubmissionSnapshot, SubmissionSnapshotMaterial


class SubmissionSnapshotMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionSnapshotMaterial
        fields = [
            'id', 'material', 'name', 'material_type', 'material_type_display',
            'description', 'is_required', 'is_completed', 'file_name', 'file_url',
            'uploaded_by_name', 'uploaded_at',
        ]


class SubmissionSnapshotSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(source='submitted_by.username', read_only=True)
    rolled_back_by_name = serializers.CharField(source='rolled_back_by.username', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    materials = SubmissionSnapshotMaterialSerializer(many=True, read_only=True)

    class Meta:
        model = SubmissionSnapshot
        fields = [
            'id', 'application', 'is_active',
            'from_status', 'to_status',
            'ps_document', 'ps_version', 'ps_title', 'ps_version_number',
            'ps_content', 'ps_word_count',
            'application_round', 'application_round_name', 'application_round_deadline',
            'submitted_by', 'submitted_by_name', 'submitted_at',
            'rolled_back_at', 'rolled_back_by', 'rolled_back_by_name',
            'rollback_reason', 'restored_status',
            'materials', 'created_at',
        ]
        read_only_fields = fields


class SubmissionSnapshotListSerializer(serializers.ModelSerializer):
    """列表精简版（不含正文与逐材料明细）。"""
    submitted_by_name = serializers.CharField(source='submitted_by.username', read_only=True)
    rolled_back_by_name = serializers.CharField(source='rolled_back_by.username', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    materials_count = serializers.IntegerField(source='materials.count', read_only=True)

    class Meta:
        model = SubmissionSnapshot
        fields = [
            'id', 'application', 'is_active',
            'from_status', 'to_status',
            'ps_title', 'ps_version_number',
            'application_round_name', 'application_round_deadline',
            'submitted_by_name', 'submitted_at',
            'rolled_back_at', 'rolled_back_by_name', 'rollback_reason',
            'restored_status', 'materials_count', 'created_at',
        ]
        read_only_fields = fields
