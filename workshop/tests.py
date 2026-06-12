from django.urls import reverse

from django.test import TestCase, override_settings

from .models import PrototypeInterest, Scenario, Vote


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class WorkshopViewsTests(TestCase):
    def set_follow_up_session(self, vote):
        session = self.client.session
        session["prototype_follow_up_vote_id"] = vote.id
        session.save()

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
        self.assertEqual(self.client.session["prototype_follow_up_vote_id"], vote.id)

    def test_thanks_page_shows_follow_up_form_after_vote_submission(self):
        open_book = Scenario.objects.get(title="Open-Book by Design")
        reward = Scenario.objects.get(title="Reward the Work")

        self.client.post(
            reverse("workshop:vote"),
            {
                "scenarios": [open_book.id, reward.id],
                "experience_rating": "4",
                "additional_comments": "",
            },
        )

        response = self.client.get(reverse("workshop:thanks"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Would you be interested in prototyping a new system I’ve built")
        self.assertContains(response, "Canvas content")

    def test_thanks_submission_records_interest_with_name_and_email(self):
        vote = Vote.objects.create(experience_rating=5, additional_comments="")
        self.set_follow_up_session(vote)

        response = self.client.post(
            reverse("workshop:thanks"),
            {"interested": "yes", "name": "Alex Example", "email": "alex@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        interest = PrototypeInterest.objects.get(vote=vote)
        self.assertTrue(interest.interested)
        self.assertEqual(interest.name, "Alex Example")
        self.assertEqual(interest.email, "alex@example.com")
        self.assertNotIn("prototype_follow_up_vote_id", self.client.session)
        self.assertContains(response, "You can close this page now.")

    def test_thanks_submission_requires_contact_details_for_interested_users(self):
        vote = Vote.objects.create(experience_rating=5, additional_comments="")
        self.set_follow_up_session(vote)

        response = self.client.post(
            reverse("workshop:thanks"),
            {"interested": "yes", "name": "", "email": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter your name.")
        self.assertContains(response, "Please enter your email.")
        self.assertFalse(PrototypeInterest.objects.filter(vote=vote).exists())

    def test_thanks_submission_records_not_interested_response(self):
        vote = Vote.objects.create(experience_rating=3, additional_comments="")
        self.set_follow_up_session(vote)

        response = self.client.post(reverse("workshop:thanks"), {"interested": "no"})

        self.assertEqual(response.status_code, 200)
        interest = PrototypeInterest.objects.get(vote=vote)
        self.assertFalse(interest.interested)
        self.assertEqual(interest.name, "")
        self.assertEqual(interest.email, "")
        self.assertContains(response, "No worries.")

    def test_completed_follow_up_does_not_create_duplicates(self):
        vote = Vote.objects.create(experience_rating=4, additional_comments="")
        PrototypeInterest.objects.create(vote=vote, interested=True, name="Alex", email="alex@example.com")
        self.set_follow_up_session(vote)

        response = self.client.get(reverse("workshop:thanks"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PrototypeInterest.objects.filter(vote=vote).count(), 1)
        self.assertContains(response, "You can close this page now.")

    def test_thanks_page_without_vote_session_shows_final_confirmation(self):
        response = self.client.get(reverse("workshop:thanks"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You can close this page now.")
        self.assertNotContains(response, "Would you be interested in prototyping")

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

    def test_results_csv_exports_vote_totals_and_percentages(self):
        paper = Scenario.objects.get(title="Back to Paper")
        open_book = Scenario.objects.get(title="Open-Book by Design")
        first_vote = Vote.objects.create(experience_rating=4, additional_comments="")
        first_vote.scenarios.set([paper, open_book])
        second_vote = Vote.objects.create(experience_rating=5, additional_comments="Best aligned.")
        second_vote.scenarios.set([open_book])

        response = self.client.get(reverse("workshop:results_csv"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="altmcq-results.csv"')
        content = response.content.decode()
        self.assertIn("scenario,votes,percent", content)
        self.assertIn("Back to Paper,1,33.3", content)
        self.assertIn("Open-Book by Design,2,66.7", content)

    def test_qr_code_endpoint_returns_png(self):
        response = self.client.get(reverse("workshop:qr_code"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG"))
