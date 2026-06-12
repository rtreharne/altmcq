import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import PrototypeInterest, Scenario, Vote


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


@admin.register(PrototypeInterest)
class PrototypeInterestAdmin(admin.ModelAdmin):
    list_display = ("submitted_at", "interested", "name", "email", "vote")
    list_filter = ("interested", "submitted_at")
    search_fields = ("name", "email")
    actions = ("export_as_csv",)

    @admin.action(description="Export selected prototype interest to CSV")
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="prototype-interest.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "interest_submitted_at",
                "interested",
                "name",
                "email",
                "vote_id",
                "vote_submitted_at",
                "experience_rating",
                "selected_scenarios",
                "additional_comments",
            ]
        )

        for interest in queryset.select_related("vote").prefetch_related("vote__scenarios").order_by("submitted_at"):
            writer.writerow(
                [
                    interest.submitted_at.isoformat(),
                    "yes" if interest.interested else "no",
                    interest.name,
                    interest.email,
                    interest.vote_id,
                    interest.vote.submitted_at.isoformat(),
                    interest.vote.experience_rating,
                    "; ".join(interest.vote.scenarios.order_by("display_order").values_list("title", flat=True)),
                    interest.vote.additional_comments,
                ]
            )

        return response
