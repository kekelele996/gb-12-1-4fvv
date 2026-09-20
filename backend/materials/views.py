from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .models import MaterialItem, MaterialTemplate
from .serializers import MaterialItemSerializer, MaterialTemplateSerializer

class MaterialItemViewSet(viewsets.ModelViewSet):
    serializer_class = MaterialItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        application_id = self.request.query_params.get('application_id')
        if application_id:
            return MaterialItem.objects.filter(application_id=application_id)

        user = self.request.user
        if user.role == 'student':
            return MaterialItem.objects.filter(application__student=user)
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            return MaterialItem.objects.filter(application__student__in=students)
        return MaterialItem.objects.all()

    def _check_not_locked(self, instance):
        if instance.is_locked:
            raise ValidationError(
                f'材料「{instance.name}」已随申请递交锁定，不能修改或移除'
            )

    def perform_update(self, serializer):
        instance = self.get_object()
        self._check_not_locked(instance)
        data = serializer.validated_data

        if 'is_completed' in data and data['is_completed'] and not instance.is_completed:
            serializer.save(
                uploaded_by=self.request.user,
                uploaded_at=timezone.now()
            )
        else:
            serializer.save()

    def perform_destroy(self, instance):
        self._check_not_locked(instance)
        instance.delete()

    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        material = self.get_object()
        if material.is_locked:
            return Response(
                {'error': f'材料「{material.name}」已随申请递交锁定，不能修改'},
                status=status.HTTP_400_BAD_REQUEST
            )
        material.is_completed = True
        material.uploaded_by = request.user
        material.uploaded_at = timezone.now()
        material.save()
        return Response(MaterialItemSerializer(material).data)

    @action(detail=True, methods=['post'])
    def mark_incomplete(self, request, pk=None):
        material = self.get_object()
        if material.is_locked:
            return Response(
                {'error': f'材料「{material.name}」已随申请递交锁定，不能修改'},
                status=status.HTTP_400_BAD_REQUEST
            )
        material.is_completed = False
        material.save()
        return Response(MaterialItemSerializer(material).data)

class MaterialTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaterialTemplate.objects.filter(is_active=True)
    serializer_class = MaterialTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def for_application(self, request):
        country = request.query_params.get('country')
        degree = request.query_params.get('degree')
        
        templates = MaterialTemplate.objects.filter(is_active=True)
        
        if country:
            templates = templates.filter(
                models.Q(countries__icontains=country) | models.Q(countries='')
            )
        
        if degree:
            templates = templates.filter(
                models.Q(degree_levels__icontains=degree) | models.Q(degree_levels='')
            )
        
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)
