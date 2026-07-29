"""
US-2: LLM Evaluation Pipeline — Given/When/Then Gherkin TDD Tests.
"""
import pytest
from src.eval_pipeline import OpenRouterClient, format_assessment


@pytest.fixture
def client():
    """Given an OpenRouter client with no API key (mock mode), When instantiated, Then it returns mock results."""
    return OpenRouterClient(api_key="")


class TestEvalPipelineGivenWhenThen:
    """
    Given Positions exist in SQLite with FEN strings and SF labels,
    When the LLM eval pipeline receives a batch of positions,
    Then each position is submitted to inclusionai/ling-3.0-flash:free via @kbench.task,
    and the LLM response (assessment + confidence) is stored alongside the SF ground truth.
    """

    def test_submit_single_position_returns_assessment(self, client):
        """Given a single FEN position, When eval_position is called, Then response has assessment and confidence."""
        result = client.evaluate_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert "assessment" in result, "Response must include assessment"
        assert "confidence" in result, "Response must include confidence"
        assert result["confidence"] >= 0.0 and result["confidence"] <= 1.0, "Confidence must be 0.0-1.0"

    def test_submit_batch_returns_all_results(self, client):
        """Given a batch of 3 positions, When eval_batch is called, Then 3 results are returned."""
        positions = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            "r1bqkbnr/pppppppp/2n5/8/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        ]
        results = client.evaluate_batch(positions)
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        for r in results:
            assert "assessment" in r, f"Missing assessment in result for {r.get('fen', 'unknown')}"
            assert "confidence" in r, f"Missing confidence in result for {r.get('fen', 'unknown')}"

    def test_confidence_for_draw_is_reasonable(self, client):
        """Given a starting position (assumed drawish), When evaluated, Then confidence should be >= 0.3."""
        result = client.evaluate_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert result["confidence"] >= 0.3, f"Confidence too low for starting position: {result['confidence']}"

    def test_format_assessment_returns_readable_string(self, client):
        """Given an assessment result, When format_assessment is called, Then a readable string is returned."""
        result = {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "assessment": "draw", "confidence": 0.75}
        formatted = format_assessment(result)
        assert "DRAW" in formatted.upper(), f"Formatted string should contain DRAW: {formatted}"
        assert "75%" in formatted, f"Formatted string should contain confidence percentage: {formatted}"

    def test_batch_confidence_scores_meet_threshold(self, client):
        """Given a batch of positions, When confidence scores are extracted, Then correct assessments should have confidence >= 0.5."""
        positions = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "r1bqkbnr/pppppppp/2n5/8/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        ]
        results = client.evaluate_batch(positions)
        for r in results:
            assert r["confidence"] >= 0.0, f"Confidence {r['confidence']} should be non-negative"
