from django.contrib import admin
from .models import ConversationLog, Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'role', 'is_authenticated', 'created_at')
    list_filter = ('role', 'is_authenticated')
    search_fields = ('phone_number', 'name')

@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display = ('sender_number', 'role', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('sender_number', 'message_body', 'chef_response')
    ordering = ('-timestamp',)
