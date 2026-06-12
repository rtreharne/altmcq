import csv
from io import BytesIO

import qrcode
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import PrototypeInterest, Scenario, Vote


SECTIONS = [
    {
        "key": "overview",
        "label": "Overview",
        "title": "Rethinking MCQ Assessment",
        "subtitle": "Facilitated by Rob Treharne and Jack Foster",
        "duration": 300,
    },
    {
        "key": "round-1-discussion",
        "label": "R1 Discuss",
        "title": "Develop the Pitch",
        "subtitle": "5 min group discussion",
        "duration": 300,
        "mode": "discussion",
        "instructions": [
            "Discuss your MCQ assessment scenario within your group.",
            "Make notes.",
            "Nominate one person from your group to deliver a 1 min pitch to the rest of the workshop.",
        ],
    },
    {
        "key": "round-1-pitches",
        "label": "R1 Pitch",
        "title": "Round 1 Pitches",
        "subtitle": "5 sec get ready + 1 min pitch per scenario group",
        "duration": 5,
        "mode": "group-timer",
        "action": "Pitch",
    },
    {
        "key": "round-1-pass",
        "label": "R1 Pass",
        "title": "Pass Your Pitch Sheet",
        "subtitle": "Move the sheet to another scenario group",
        "duration": 30,
        "mode": "pass",
        "instruction": "Pass your pitch sheet to another group now.",
    },
    {
        "key": "round-2-discussion",
        "label": "R2 Discuss",
        "title": "Anti-Pitch",
        "subtitle": "5 min group discussion",
        "duration": 300,
        "mode": "discussion",
        "instructions": [
            "Discuss the alternative assessment scenario within your group.",
            "Use the rubric to assess the scenario.",
            "Nominate one person from your group to deliver a 1 min anti-pitch to the rest of the workshop.",
        ],
    },
    {
        "key": "round-2-pitches",
        "label": "R2 Anti-Pitch",
        "title": "Round 2 Anti-Pitches",
        "subtitle": "5 sec get ready + 1 min anti-pitch per scenario group",
        "duration": 5,
        "mode": "group-timer",
        "action": "Anti-pitch",
    },
    {
        "key": "round-2-pass",
        "label": "R2 Pass",
        "title": "Pass Your Pitch Sheet",
        "subtitle": "Move the sheet to another scenario group",
        "duration": 30,
        "mode": "pass",
        "instruction": "Please pass your scenario back to the original group.",
    },
    {
        "key": "round-3-discussion",
        "label": "R3 Discuss",
        "title": "Rebuttal",
        "subtitle": "5 min group discussion",
        "duration": 300,
        "mode": "discussion",
        "instructions": [
            "Discuss the anti-pitch made against your original assessment scenario.",
            "Prepare a rebuttal that strengthens your original pitch.",
            "Nominate one person from your group to deliver the 1 min rebuttal.",
        ],
    },
    {
        "key": "round-3-pitches",
        "label": "R3 Rebuttal",
        "title": "Round 3 Rebuttals",
        "subtitle": "5 sec get ready + 1 min rebuttal per scenario group",
        "duration": 5,
        "mode": "group-timer",
        "action": "Rebuttal",
    },
    {
        "key": "vote",
        "label": "Vote",
        "title": "Individual Vote and Feedback",
        "subtitle": "5 min individual vote and feedback form",
        "duration": 300,
        "mode": "vote",
    },
    {
        "key": "results",
        "label": "Results",
        "title": "Results",
        "subtitle": "1 min summary",
        "duration": 60,
    },
]

FOLLOW_UP_VOTE_SESSION_KEY = "prototype_follow_up_vote_id"


def build_nav_groups(sections):
    groups = []
    round_titles = {
        "round-1": "Round 1",
        "round-2": "Round 2",
        "round-3": "Round 3",
    }

    for index, section in enumerate(sections):
        round_key = next((key for key in round_titles if section["key"].startswith(key)), None)
        if round_key:
            if not groups or groups[-1].get("round_key") != round_key:
                groups.append(
                    {
                        "round_key": round_key,
                        "title": round_titles[round_key],
                        "items": [],
                    }
                )
            groups[-1]["items"].append(
                {
                    "index": index,
                    "label": section["label"].replace("R1 ", "").replace("R2 ", "").replace("R3 ", ""),
                }
            )
        else:
            groups.append(
                {
                    "title": section["label"],
                    "items": [
                        {
                            "index": index,
                            "label": section["label"],
                        }
                    ],
                }
            )

    return groups


def facilitator(request):
    scenarios = list(Scenario.objects.all())
    vote_url = request.build_absolute_uri(reverse("workshop:vote"))
    return render(
        request,
        "workshop/facilitator.html",
        {
            "sections": SECTIONS,
            "nav_groups": build_nav_groups(SECTIONS),
            "scenarios": scenarios,
            "scenario_titles": [scenario.title for scenario in scenarios],
            "vote_url": vote_url,
        },
    )


def vote(request):
    scenarios = Scenario.objects.all()
    if request.method == "POST":
        scenario_ids = request.POST.getlist("scenarios")
        rating = request.POST.get("experience_rating")
        additional_comments = request.POST.get("additional_comments", "").strip()
        selected_scenarios = list(Scenario.objects.filter(id__in=scenario_ids))
        if len(selected_scenarios) == 2 and rating in {"1", "2", "3", "4", "5"}:
            vote = Vote.objects.create(
                experience_rating=int(rating),
                additional_comments=additional_comments[:1000],
            )
            vote.scenarios.set(selected_scenarios)
            request.session[FOLLOW_UP_VOTE_SESSION_KEY] = vote.id
            return redirect("workshop:thanks")

    return render(
        request,
        "workshop/vote.html",
        {
            "scenarios": scenarios,
        },
    )


def build_thanks_context(*, show_form=False, errors=None, form_data=None, completed=False, no_worries=False):
    return {
        "show_form": show_form,
        "errors": errors or {},
        "form_data": form_data or {},
        "completed": completed,
        "no_worries": no_worries,
    }


def thanks(request):
    vote_id = request.session.get(FOLLOW_UP_VOTE_SESSION_KEY)
    vote = Vote.objects.filter(id=vote_id).first() if vote_id else None
    interest = PrototypeInterest.objects.filter(vote=vote).first() if vote else None

    if request.method == "POST":
        if not vote or interest:
            request.session.pop(FOLLOW_UP_VOTE_SESSION_KEY, None)
            return render(request, "workshop/thanks.html", build_thanks_context(completed=True))

        interested_value = request.POST.get("interested")
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        form_data = {
            "interested": interested_value,
            "name": name,
            "email": email,
        }
        errors = {}

        if interested_value not in {"yes", "no"}:
            errors["interested"] = "Please choose yes or no."
        elif interested_value == "yes":
            if not name:
                errors["name"] = "Please enter your name."
            if not email:
                errors["email"] = "Please enter your email."
            else:
                try:
                    validate_email(email)
                except ValidationError:
                    errors["email"] = "Please enter a valid email address."

        if errors:
            return render(
                request,
                "workshop/thanks.html",
                build_thanks_context(show_form=True, errors=errors, form_data=form_data),
            )

        PrototypeInterest.objects.create(
            vote=vote,
            interested=interested_value == "yes",
            name=name[:120] if interested_value == "yes" else "",
            email=email if interested_value == "yes" else "",
        )
        request.session.pop(FOLLOW_UP_VOTE_SESSION_KEY, None)
        return render(
            request,
            "workshop/thanks.html",
            build_thanks_context(completed=True, no_worries=interested_value == "no"),
        )

    if vote and not interest:
        return render(request, "workshop/thanks.html", build_thanks_context(show_form=True))

    request.session.pop(FOLLOW_UP_VOTE_SESSION_KEY, None)
    return render(request, "workshop/thanks.html", build_thanks_context(completed=True, no_worries=bool(interest and not interest.interested)))


def results(request):
    scenarios = Scenario.objects.annotate(vote_count=Count("votes", distinct=True)).order_by("display_order")
    total = sum(scenario.vote_count for scenario in scenarios)
    payload = []
    for scenario in scenarios:
        percent = round((scenario.vote_count / total) * 100, 1) if total else 0
        payload.append(
            {
                "id": scenario.id,
                "title": scenario.title,
                "votes": scenario.vote_count,
                "percent": percent,
            }
        )

    return JsonResponse({"total": total, "scenarios": payload})


def results_csv(request):
    scenarios = Scenario.objects.annotate(vote_count=Count("votes", distinct=True)).order_by("display_order")
    total = sum(scenario.vote_count for scenario in scenarios)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="altmcq-results.csv"'

    writer = csv.writer(response)
    writer.writerow(["scenario", "votes", "percent"])
    for scenario in scenarios:
        percent = round((scenario.vote_count / total) * 100, 1) if total else 0
        writer.writerow([scenario.title, scenario.vote_count, percent])

    return response


def qr_code(request):
    url = request.build_absolute_uri(reverse("workshop:vote"))
    image = qrcode.make(url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")
