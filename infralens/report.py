from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

from infralens.rules import Finding, RecommendationResult
from infralens.scoring import ScoreResult


class PDFReport(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "InfraLens MVP Report", ln=True)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 7, datetime.now().strftime("Generated: %Y-%m-%d %H:%M:%S"), ln=True)
        self.ln(2)


def _write_multiline(pdf: FPDF, text: str, line_height: int = 6) -> None:
    # Keep writes anchored to left margin so effective width never becomes zero.
    if getattr(pdf, "_unicode_enabled", False):
        safe_text = text
    else:
        safe_text = text.encode("latin-1", "replace").decode("latin-1")
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, line_height, safe_text)


def _enable_unicode_font(pdf: FPDF) -> tuple[bool, str]:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    for path in candidates:
        if not Path(path).exists():
            continue
        try:
            pdf.add_font("InfraUnicode", "", path)
            return True, "InfraUnicode"
        except Exception:
            continue
    return False, "Helvetica"


def build_pdf_report(
    scenario_name: str,
    score: ScoreResult,
    findings: list[Finding],
    analysis_text: str,
    recommendation: RecommendationResult,
    recommendation_text: str,
    labels: dict[str, str] | None = None,
    expected_line: str | None = None,
) -> bytes:
    lbl = labels or {
        "scenario": "Scenario",
        "efficiency": "Efficiency Score",
        "component_scores": "Component Scores",
        "gpu_component": "GPU component",
        "numa_component": "NUMA component",
        "network_component": "Network I/O component",
        "findings": "Bottleneck Findings",
        "analysis": "Analysis Narrative",
        "placement": "Placement Recommendation",
        "expected": "Expected improvement",
    }

    pdf = PDFReport()
    unicode_enabled, font_family = _enable_unicode_font(pdf)
    setattr(pdf, "_unicode_enabled", unicode_enabled)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font(font_family, "B" if font_family == "Helvetica" else "", 12)
    pdf.cell(0, 8, f"{lbl['scenario']}: {scenario_name}", ln=True)
    pdf.cell(0, 8, f"{lbl['efficiency']}: {score.score}/100 ({score.grade})", ln=True)
    pdf.ln(3)

    pdf.set_font(font_family, "B" if font_family == "Helvetica" else "", 11)
    pdf.cell(0, 8, lbl["component_scores"], ln=True)
    pdf.set_font(font_family, "", 10)
    _write_multiline(
        pdf,
        (
            f"{lbl['gpu_component']}: {score.gpu_score:.2f}\n"
            f"{lbl['numa_component']}: {score.numa_score:.2f}\n"
            f"{lbl['network_component']}: {score.network_score:.2f}"
        ),
    )
    pdf.ln(2)

    pdf.set_font(font_family, "B" if font_family == "Helvetica" else "", 11)
    pdf.cell(0, 8, lbl["findings"], ln=True)
    pdf.set_font(font_family, "", 10)
    for finding in findings:
        _write_multiline(pdf, f"- [{finding.category}] {finding.message}")

    pdf.ln(2)
    pdf.set_font(font_family, "B" if font_family == "Helvetica" else "", 11)
    pdf.cell(0, 8, lbl["analysis"], ln=True)
    pdf.set_font(font_family, "", 10)
    _write_multiline(pdf, analysis_text)

    pdf.ln(2)
    pdf.set_font(font_family, "B" if font_family == "Helvetica" else "", 11)
    pdf.cell(0, 8, lbl["placement"], ln=True)
    pdf.set_font(font_family, "", 10)
    for idx, item in enumerate(recommendation.items, 1):
        _write_multiline(pdf, f"{idx}. {item.workload}: {item.action}")

    if expected_line is None:
        expected_line = (
            f"{lbl['expected']}: utilization {recommendation.expected_util_before}% -> "
            f"{recommendation.expected_util_after}%, training +{recommendation.expected_training_gain_pct}%, "
            f"latency -{recommendation.expected_latency_drop_pct}%"
        )
    _write_multiline(pdf, expected_line)
    pdf.ln(2)
    _write_multiline(pdf, recommendation_text)

    return bytes(pdf.output(dest="S"))
