from django.db import migrations, models


def copy_existing_scenario_votes(apps, schema_editor):
    Vote = apps.get_model("workshop", "Vote")
    through_model = Vote.scenarios.through
    rows = []
    for vote in Vote.objects.exclude(scenario_id=None):
        rows.append(through_model(vote_id=vote.id, scenario_id=vote.scenario_id))
    through_model.objects.bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("workshop", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="vote",
            old_name="feedback",
            new_name="additional_comments",
        ),
        migrations.AddField(
            model_name="vote",
            name="experience_rating",
            field=models.PositiveSmallIntegerField(default=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="vote",
            name="scenarios",
            field=models.ManyToManyField(related_name="votes", to="workshop.scenario"),
        ),
        migrations.RunPython(copy_existing_scenario_votes, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="vote",
            name="scenario",
        ),
    ]
