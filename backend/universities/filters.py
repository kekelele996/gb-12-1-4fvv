import django_filters
from .models import University, Program

class UniversityFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(lookup_expr='iexact')
    min_ranking = django_filters.NumberFilter(field_name='qs_ranking', lookup_expr='gte')
    max_ranking = django_filters.NumberFilter(field_name='qs_ranking', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = University
        fields = ['country', 'city']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(description__icontains=value)
        )

class ProgramFilter(django_filters.FilterSet):
    university = django_filters.NumberFilter(field_name='university__id')
    degree_level = django_filters.CharFilter()
    min_tuition = django_filters.NumberFilter(field_name='tuition', lookup_expr='gte')
    max_tuition = django_filters.NumberFilter(field_name='tuition', lookup_expr='lte')
    
    class Meta:
        model = Program
        fields = ['degree_level']

import django_filters
