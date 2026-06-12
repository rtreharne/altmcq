#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = ROOT / "scenarios"
OUTPUT_DIR = ROOT / "scenario_pdfs"


def lines_between(text: str, start: str, end: str | None = None) -> list[str]:
    pattern = rf"^## {re.escape(start)}\n(.*?)(?=^## {re.escape(end)}\n|\Z)" if end else rf"^## {re.escape(start)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return []
    return [line.strip() for line in match.group(1).strip().splitlines() if line.strip()]


def bullets(section_lines: list[str]) -> list[str]:
    return [line[2:].strip() for line in section_lines if line.startswith("- ")]


def first_paragraph(lines: list[str]) -> str:
    return next((line for line in lines if not line.startswith("- ") and not line.startswith("|")), "")


def parse_markdown(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    title = lines[0].removeprefix("# ").strip()
    description = next(line for line in lines[1:] if line)
    return {
        "title": title,
        "description": description,
        "how_it_works": bullets(lines_between(text, "How It Works")),
        "shared_assumptions": bullets(lines_between(text, "Shared Assumptions")),
        "round_1": first_paragraph(lines_between(text, "Round 1: Develop Your Pitch")),
        "round_2": first_paragraph(lines_between(text, "Round 2: Anti-Pitch Notes")),
        "round_3": first_paragraph(lines_between(text, "Round 3: Rebuttal Notes")),
    }


def make_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ScenarioTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            spaceAfter=6,
            textColor=colors.HexColor("#17211b"),
        ),
        "heading": ParagraphStyle(
            "ScenarioHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            spaceBefore=7,
            spaceAfter=4,
            textColor=colors.HexColor("#0c6b58"),
        ),
        "body": ParagraphStyle(
            "ScenarioBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=11,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "ScenarioSmall",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=9,
        ),
    }


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("&", "&amp;"), style)


def bullet_list(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(paragraph(item, style), leftIndent=3 * mm) for item in items],
        bulletType="bullet",
        leftIndent=4 * mm,
        bulletFontSize=6,
    )


def rubric_table(styles: dict[str, ParagraphStyle]) -> Table:
    criteria = [
        ("Learning value", "Does it encourage meaningful learning?"),
        ("Validity", "Does the mark provide credible evidence of understanding?"),
        ("Fairness", "Is it equitable and inclusive?"),
        ("AI resilience", "Does it remain credible when students can use AI?"),
        ("Practicality", "Is it manageable for more than 500 students?"),
    ]
    data = [[paragraph("<b>Criterion</b>", styles["small"]), paragraph("<b>Key question</b>", styles["small"]), "1", "2", "3", "4", "5"]]
    for criterion, question in criteria:
        data.append([
            paragraph(criterion, styles["small"]),
            paragraph(question, styles["small"]),
            "",
            "",
            "",
            "",
            "",
        ])

    table = Table(data, colWidths=[29 * mm, 76 * mm, 9 * mm, 9 * mm, 9 * mm, 9 * mm, 9 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8d2c3")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f1ea")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (2, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (2, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def notes_box(label: str, height: float, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table(
        [[paragraph(f"<b>{label}</b>", styles["small"])], [""]],
        colWidths=[160 * mm],
        rowHeights=[8 * mm, height],
    )
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8d2c3")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f1ea")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def scenario_story(scenario: dict[str, object], styles: dict[str, ParagraphStyle]) -> list:
    return [
        paragraph(str(scenario["title"]), styles["title"]),
        paragraph(str(scenario["description"]), styles["body"]),
        paragraph("How It Works", styles["heading"]),
        bullet_list(scenario["how_it_works"], styles["body"]),
        paragraph("Shared Assumptions", styles["heading"]),
        bullet_list(scenario["shared_assumptions"], styles["body"]),
        paragraph("Round 1: Develop Your Pitch", styles["heading"]),
        paragraph(str(scenario["round_1"]), styles["body"]),
        notes_box("Pitch notes", 34 * mm, styles),
        PageBreak(),
        paragraph(f"Evaluate: {scenario['title']}", styles["title"]),
        paragraph(
            "Score each criterion from 1 to 5. Scale definitions: 1 = very weak, 2 = weak, 3 = mixed, 4 = strong, 5 = very strong. Total possible score: 25.",
            styles["body"],
        ),
        rubric_table(styles),
        Spacer(1, 4 * mm),
        paragraph("<b>Total score: ________ / 25</b>", styles["body"]),
        Spacer(1, 3 * mm),
        notes_box("Strongest feature", 14 * mm, styles),
        Spacer(1, 3 * mm),
        notes_box("Biggest weakness", 14 * mm, styles),
        Spacer(1, 2 * mm),
        paragraph("Round 2: Anti-Pitch Notes", styles["heading"]),
        paragraph(str(scenario["round_2"]), styles["body"]),
        notes_box("Anti-pitch notes", 24 * mm, styles),
        Spacer(1, 2 * mm),
        paragraph("Round 3: Rebuttal Notes", styles["heading"]),
        paragraph(str(scenario["round_3"]), styles["body"]),
        notes_box("Rebuttal notes", 24 * mm, styles),
    ]


def make_document(output_path: Path, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=title,
    )


def build_pdf(markdown_path: Path, output_dir: Path) -> Path:
    scenario = parse_markdown(markdown_path)
    styles = make_styles()
    output_path = output_dir / f"{markdown_path.stem}.pdf"
    doc = make_document(output_path, str(scenario["title"]))
    story = scenario_story(scenario, styles)
    doc.build(story)
    return output_path


def build_consolidated_pdf(markdown_paths: list[Path], output_dir: Path) -> Path:
    styles = make_styles()
    output_path = output_dir / "all-scenarios.pdf"
    doc = make_document(output_path, "All MCQ Assessment Scenarios")
    story = []
    for index, markdown_path in enumerate(markdown_paths):
        if index:
            story.append(PageBreak())
        story.extend(scenario_story(parse_markdown(markdown_path), styles))
    doc.build(story)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate printable scenario PDFs from Markdown files.")
    parser.add_argument("--input-dir", type=Path, default=SCENARIOS_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    markdown_paths = sorted(args.input_dir.glob("*.md"))
    for markdown_path in markdown_paths:
        output_path = build_pdf(markdown_path, args.output_dir)
        print(output_path.relative_to(ROOT))
    consolidated_path = build_consolidated_pdf(markdown_paths, args.output_dir)
    print(consolidated_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
