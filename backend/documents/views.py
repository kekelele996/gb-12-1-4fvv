from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from diff_match_patch import diff_match_patch
from .models import Document, DocumentVersion, DocumentComment
from .serializers import (
    DocumentSerializer, DocumentVersionSerializer, DocumentCommentSerializer
)

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        application_id = self.request.query_params.get('application_id')
        
        if application_id:
            return Document.objects.filter(application_id=application_id)
        
        if user.role == 'student':
            return Document.objects.filter(application__student=user)
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            return Document.objects.filter(application__student__in=students)
        return Document.objects.all()

class DocumentVersionViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        document_id = self.request.query_params.get('document_id')
        if document_id:
            return DocumentVersion.objects.filter(document_id=document_id)
        return DocumentVersion.objects.all()
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        document_id = request.data.get('document')
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
        
        previous_version = document.versions.order_by('-version_number').first()
        
        data = request.data.copy()
        data['created_by'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        new_version = serializer.save(created_by=request.user)
        
        if previous_version:
            dmp = diff_match_patch()
            diffs = dmp.diff_main(previous_version.content, new_version.content)
            dmp.diff_cleanupSemantic(diffs)
            patches = dmp.patch_make(previous_version.content, diffs)
            new_version.diff_from_previous = dmp.patch_toText(patches)
            new_version.save()
        
        document.current_version = new_version
        document.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        current_version = self.get_object()
        compare_with_id = request.query_params.get('compare_with')
        
        try:
            compare_version = DocumentVersion.objects.get(id=compare_with_id)
        except DocumentVersion.DoesNotExist:
            return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)
        
        dmp = diff_match_patch()
        diffs = dmp.diff_main(compare_version.content, current_version.content)
        dmp.diff_cleanupSemantic(diffs)
        
        return Response({
            'diffs': [{'operation': d[0], 'text': d[1]} for d in diffs],
            'current_version': DocumentVersionSerializer(current_version).data,
            'compare_version': DocumentVersionSerializer(compare_version).data
        })

class DocumentCommentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        document_id = self.request.query_params.get('document_id')
        if document_id:
            return DocumentComment.objects.filter(document_id=document_id, parent__isnull=True)
        return DocumentComment.objects.filter(parent__isnull=True)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        comment = self.get_object()
        comment.is_resolved = True
        comment.save()
        return Response(DocumentCommentSerializer(comment).data)
