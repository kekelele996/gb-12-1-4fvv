from rest_framework import serializers
from .models import MaterialItem, MaterialTemplate

class MaterialItemSerializer(serializers.ModelSerializer):
    material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = MaterialItem
        fields = ['id', 'application', 'name', 'material_type', 
                  'material_type_display', 'description', 'is_required',
                  'is_completed', 'file', 'uploaded_by', 'uploaded_by_name',
                  'uploaded_at', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'created_at', 'updated_at']

class MaterialTemplateSerializer(serializers.ModelSerializer):
    material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    
    class Meta:
        model = MaterialTemplate
        fields = ['id', 'material_type', 'material_type_display', 
                  'name', 'description', 'is_required', 'countries',
                  'degree_levels', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
