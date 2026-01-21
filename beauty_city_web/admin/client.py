from django.contrib import admin


class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "registration_date", "appointments_count")
    search_fields = ("name", "phone", "email")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset

    def appointments_count(self, obj):
        return obj.appointments.count()

    appointments_count.short_description = "Количество записей"
