from django.contrib import admin
from .models import College

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'status', 'get_user_count', 'get_event_count', 'created_at']
    list_filter   = ['status']
    search_fields = ['name', 'slug', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
