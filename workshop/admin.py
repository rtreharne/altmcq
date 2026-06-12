from django.contrib import admin

from .models import Scenario, Vote


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("display_order", "title")
    ordering = ("display_order",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("submitted_at", "experience_rating")
    list_filter = ("experience_rating", "submitted_at")
    search_fields = ("additional_comments",)
    filter_horizontal = ("scenarios",)
