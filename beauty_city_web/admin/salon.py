from django.contrib import admin
from ..forms.salon import SalonForm

class SalonAdmin(admin.ModelAdmin):
    form = SalonForm
    
    list_display = ("name", "address", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address", "phone")
    list_editable = ("is_active",)
