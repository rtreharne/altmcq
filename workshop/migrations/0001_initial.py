# Generated manually for the workshop facilitator app.

from django.db import migrations, models
import django.db.models.deletion


SCENARIOS = [
    {
        "title": "Back to Paper",
        "short_description": "Students complete a traditional paper-based MCQ test under invigilated conditions.",
        "how_it_works": [
            "Students sit a timed on-campus assessment without access to phones, laptops, notes, or other resources.",
            "Multiple versions of the paper can be created by changing question and answer-option order.",
            "Answer sheets are marked manually or processed using optical mark recognition.",
            "Online quizzes may support practice, but the paper test determines the summative mark.",
        ],
    },
    {
        "title": "Detect and Deter",
        "short_description": "Students complete an online MCQ assessment, with safeguards used to discourage inappropriate use of AI.",
        "how_it_works": [
            "Students complete a timed online assessment with randomised questions and answer options.",
            "Strict time limits and clear academic-integrity guidance act as deterrents.",
            "Activity logs are reviewed for unusual patterns, such as very rapid completion or repeated navigation away from the page.",
            "Suspicious cases may trigger a follow-up discussion, an additional task, or an academic-integrity investigation.",
        ],
    },
    {
        "title": "Practice, Track, Validate",
        "short_description": "Students build a record of performance through regular practice, confirmed through a short invigilated validation exercise.",
        "how_it_works": [
            "Students complete frequent low-stakes MCQ practice throughout the module.",
            "Questions are dynamically generated or selected from a large bank to reduce memorisation.",
            "The system tracks engagement, topic coverage, accuracy, improvement, and consistency over time.",
            "A short invigilated activity confirms that the longer-term record is credible.",
        ],
    },
    {
        "title": "Open-Book by Design",
        "short_description": "Students may use AI and other resources, but questions reward application and critical judgement.",
        "how_it_works": [
            "Students may use notes, textbooks, websites, and generative AI tools during the assessment.",
            "Questions focus on unfamiliar cases, interpretation, evaluation, and decision-making.",
            "Students may be asked to critique an AI-generated answer or choose between several plausible explanations.",
            "MCQs can be combined with short justifications, confidence ratings, or follow-up questions.",
        ],
    },
    {
        "title": "Reward the Work",
        "short_description": "Students earn marks through sustained MCQ practice, with regular limits rewarding consistent engagement.",
        "how_it_works": [
            "The module is divided into weekly or fortnightly windows, each with a fixed amount of credit available.",
            "Students earn marks for correctly answering a defined number of questions within each window.",
            "Credit is capped by topic or learning objective to encourage breadth and prevent easy-question farming.",
            "A limited number of missed windows can be discounted or recovered to account for short-term disruption.",
        ],
    },
]


def seed_scenarios(apps, schema_editor):
    Scenario = apps.get_model("workshop", "Scenario")
    for index, scenario in enumerate(SCENARIOS, start=1):
        Scenario.objects.update_or_create(
            display_order=index,
            defaults={
                "title": scenario["title"],
                "short_description": scenario["short_description"],
                "how_it_works": scenario["how_it_works"],
            },
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Scenario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("short_description", models.TextField()),
                ("how_it_works", models.JSONField(default=list)),
                ("display_order", models.PositiveSmallIntegerField(unique=True)),
            ],
            options={
                "ordering": ["display_order"],
            },
        ),
        migrations.CreateModel(
            name="Vote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("feedback", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "scenario",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="workshop.scenario"),
                ),
            ],
            options={
                "ordering": ["-submitted_at"],
            },
        ),
        migrations.RunPython(seed_scenarios, migrations.RunPython.noop),
    ]
