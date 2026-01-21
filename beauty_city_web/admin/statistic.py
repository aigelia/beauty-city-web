from django.contrib import admin


class StatisticAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "total_appointments",
        "completed_appointments",
        "total_revenue",
        "new_clients",
    )
    ordering = ("-date",)
    date_hierarchy = "date"
