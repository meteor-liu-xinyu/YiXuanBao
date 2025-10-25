from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
import csv
from .models import Hospital


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    """
    Enhanced admin for Hospital:
    - improved list display including key scoring fields
    - filters for quick narrowing
    - search_fields extended
    - list_editable for quick inline edits
    - fieldsets grouping to make editing easier
    - readonly timestamps
    - CSV export action for selected hospitals
    - clickable map link (when coordinates exist)
    """
    list_display = (
        'name',
        'region',
        'grade_level',
        'specialty',
        'avg_cost',
        'bed_count',
        'specialty_score',
        'success_rate',
        'equipment_score',
        'reputation_index',
        'map_link',
    )
    list_filter = ('region', 'grade_level', 'specialty')
    search_fields = ('name', 'region', 'specialty', 'contact')
    list_editable = ('grade_level', 'avg_cost')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic information', {
            'fields': ('name', 'region', 'specialty', 'address', 'contact')
        }),
        ('Location', {
            'fields': ('longitude', 'latitude', 'map_link'),
        }),
        ('Capacity & cost', {
            'fields': ('avg_cost', 'bed_count', 'avg_wait_hours'),
        }),
        ('Scores & stats', {
            'fields': ('grade_level', 'specialty_score', 'equipment_score', 'success_rate', 'reputation_index'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    actions = ['export_selected_as_csv']

    def map_link(self, obj):
        """Return a clickable Google Maps link when coordinates are present."""
        if obj.latitude is None or obj.longitude is None:
            return '-'
        url = f"https://www.google.com/maps/search/?api=1&query={obj.latitude},{obj.longitude}"
        return format_html('<a href="{}" target="_blank">地图</a>', url)
    map_link.short_description = '地图'

    def export_selected_as_csv(self, request, queryset):
        """
        Export selected hospitals to CSV.
        The CSV includes key fields and scoring-related fields so it can be used for offline analysis.
        """
        fieldnames = [
            'id', 'name', 'region', 'specialty', 'address', 'contact',
            'grade_level', 'longitude', 'latitude', 'avg_cost', 'bed_count',
            'specialty_score', 'success_rate', 'avg_wait_hours',
            'equipment_score', 'reputation_index', 'created_at', 'updated_at'
        ]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=hospitals_export.csv'
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        for h in queryset:
            writer.writerow({
                'id': h.id,
                'name': h.name,
                'region': h.region,
                'specialty': h.specialty,
                'address': h.address,
                'contact': h.contact,
                'grade_level': h.grade_level,
                'longitude': h.longitude,
                'latitude': h.latitude,
                'avg_cost': h.avg_cost,
                'bed_count': h.bed_count,
                'specialty_score': h.specialty_score,
                'success_rate': h.success_rate,
                'avg_wait_hours': h.avg_wait_hours,
                'equipment_score': h.equipment_score,
                'reputation_index': h.reputation_index,
                'created_at': h.created_at,
                'updated_at': h.updated_at,
            })
        return response
    export_selected_as_csv.short_description = "导出所选医院为 CSV"

    # Make sure the map_link column is safe for sorting/filters even if it's computed.
    map_link.admin_order_field = 'latitude'