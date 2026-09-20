from rest_framework import serializers
from .models import Document, DocumentVersion, DocumentComment

class DocumentCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentComment
        fields = ['id', 'document', 'version', 'author', 'author_name',
                  'content', 'start_position', 'end_position',
                  'highlighted_text', 'is_resolved', 'parent',
                  'replies', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return DocumentCommentSerializer(obj.replies.all(), many=True).data
        return []
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'version_number', 'content', 'file',
                  'word_count', 'created_by', 'created_by_name',
                  'change_note', 'diff_from_previous', 'created_at']
        read_only_fields = ['id', 'document', 'version_number', 
                           'word_count', 'created_by', 'created_at']

class DocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    current_version = DocumentVersionSerializer(read_only=True)
    versions_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Document
        fields = ['id', 'application', 'document_type', 'document_type_display',
                  'title', 'description', 'file', 'current_version',
                  'versions_count', 'comments_count',
                  'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'current_version', 'versions_count', 
                           'comments_count', 'created_by', 'created_at', 'updated_at']
    
    def get_versions_count(self, obj):
        return obj.versions.count()
    
    def get_comments_count(self, obj):
        return obj.comments.filter(is_resolved=False).count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
