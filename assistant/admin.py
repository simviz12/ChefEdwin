from django.contrib import admin
from .models import ConversationLog, Student
import hashlib

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'role', 'is_authenticated', 'created_at')
    list_filter = ('role', 'is_authenticated')
    search_fields = ('phone_number', 'name')
    
    def save_model(self, request, obj, form, change):
        """
        Override save to automatically hash password if it's being set/changed
        """
        # Check if password field was modified and is not already hashed
        if 'password' in form.changed_data or not change:
            raw_password = obj.password
            # Only hash if it doesn't look like a hash already (SHA-256 is 64 chars)
            if raw_password and len(raw_password) != 64:
                obj.password = hashlib.sha256(raw_password.encode()).hexdigest()
                self.message_user(request, f"Password hashed successfully for {obj.phone_number}")
        
        super().save_model(request, obj, form, change)

@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display = ('sender_number', 'role', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('sender_number', 'message_body', 'chef_response')
    ordering = ('-timestamp',)
