from django.urls import reverse

from django.test import TestCase

from .models import Scenario, Vote


class WorkshopViewsTests(TestCase):
    def test_facilitator_page_loads_without_clutter_panels(self):
        response = self.client.get(reverse("workshop:facilitator"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rethinking MCQ Assessment")
        self.assertContains(response, "Round 1")
        self.assertNotContains(response, "Scenario groups")
        self.assertNotContains(response, "Evaluation criteria")

    def test_vote_submission_records_vote_and_redirects_to_confirmation(self):
        open_book = Scenario.objects.get(title="Open-Book by Design")
        practice = Scenario.objects.get(title="Practice, Track, Validate")

        response = self.client.post(
            reverse("workshop:vote"),
            {
                "scenarios": [open_book.id, practice.id],
                "experience_rating": "5",
                "additional_comments": "Most defensible at scale.",
            },
        )

        self.assertRedirects(response, reverse("workshop:thanks"))
        vote = Vote.objects.get()
        self.assertEqual(set(vote.scenarios.all()), {open_book, practice})
        self.assertEqual(vote.experience_rating, 5)
        self.assertEqual(vote.additional_comments, "Most defensible at scale.")

    def test_results_report_totals_and_percentages_without_comments(self):
        paper = Scenario.objects.get(title="Back to Paper")
        open_book = Scenario.objects.get(title="Open-Book by Design")
        first_vote = Vote.objects.create(experience_rating=4, additional_comments="")
        first_vote.scenarios.set([paper, open_book])
        second_vote = Vote.objects.create(experience_rating=5, additional_comments="Best aligned.")
        second_vote.scenarios.set([open_book])

        response = self.client.get(reverse("workshop:results"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 3)
        by_title = {item["title"]: item for item in data["scenarios"]}
        self.assertEqual(by_title["Back to Paper"]["votes"], 1)
        self.assertEqual(by_title["Back to Paper"]["percent"], 33.3)
        self.assertEqual(by_title["Open-Book by Design"]["votes"], 2)
        self.assertEqual(by_title["Open-Book by Design"]["percent"], 66.7)
        self.assertNotIn("comments", data)

    def test_qr_code_endpoint_returns_png(self):
        response = self.client.get(reverse("workshop:qr_code"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG"))
