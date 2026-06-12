from django.db import models


class Scenario(models.Model):
    title = models.CharField(max_length=120)
    short_description = models.TextField()
    how_it_works = models.JSONField(default=list)
    display_order = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title


class Vote(models.Model):
    scenarios = models.ManyToManyField(Scenario, related_name="votes")
    experience_rating = models.PositiveSmallIntegerField()
    additional_comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Vote submitted at {self.submitted_at:%Y-%m-%d %H:%M}"


class PrototypeInterest(models.Model):
    vote = models.OneToOneField(Vote, on_delete=models.CASCADE, related_name="prototype_interest")
    interested = models.BooleanField()
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        status = "Interested" if self.interested else "Not interested"
        return f"{status} follow-up for vote {self.vote_id}"
