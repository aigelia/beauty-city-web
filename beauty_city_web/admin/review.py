from django.contrib import admin


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "text",
        "rating",
    )
    ordering = ("-date",)
    date_hierarchy = "date"
