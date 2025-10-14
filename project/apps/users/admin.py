from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('is_admin', 'avatar', 'phone_number')}),
    )
    list_display = ('username', 'email', 'is_admin', 'is_staff', 'is_active')
