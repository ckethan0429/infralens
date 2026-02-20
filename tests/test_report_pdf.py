import unittest
from unittest.mock import patch

from infralens.report import build_pdf_report
from infralens.rules import Finding, RecommendationResult
from infralens.scoring import ScoreResult


class ReportPdfTests(unittest.TestCase):
    @patch("infralens.report._enable_unicode_font", return_value=(False, "Helvetica"))
    def test_pdf_build_does_not_crash_with_korean_labels_on_latin_font(self, _mock_font):
        score = ScoreResult(
            score=72,
            grade="B",
            gpu_score=0.72,
            numa_score=0.80,
            network_score=0.68,
            profile="default",
        )
        findings = [Finding(category="MIG", severity="medium", message="한글 메시지 테스트", code="mig_opportunity")]
        recommendation = RecommendationResult(
            items=[],
            expected_util_before=52,
            expected_util_after=78,
            expected_training_gain_pct=12,
            expected_latency_drop_pct=18,
        )
        labels = {
            "scenario": "시나리오",
            "efficiency": "효율 점수",
            "component_scores": "구성 점수",
            "gpu_component": "GPU 구성 점수",
            "numa_component": "NUMA 구성 점수",
            "network_component": "네트워크 I/O 점수",
            "findings": "병목/비효율 분석 결과",
            "analysis": "AI 병목/비효율 분석",
            "placement": "최적 배치 제안",
            "expected": "예상 개선",
        }

        data = build_pdf_report(
            scenario_name="한글 시나리오",
            score=score,
            findings=findings,
            analysis_text="분석 내용",
            recommendation=recommendation,
            recommendation_text="추천 설명",
            labels=labels,
        )

        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main()
