from django.contrib import admin
from .models import Hospital

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'specialty', 'contact')
    search_fields = ('name','region','specialty')