"""
US-3: Metrics Computation Engine (ECE, resignation, gambling)
Given/When/Then Gherkin TDD tests + implementation.
"""
import math
import pytest


def compute_ece(confidences: list[float], accuracies: list[bool], n_bins: int = 10) -> float:
    """
    Given confidence scores and binary accuracies,
    When ECE is computed, Then the Expected Calibration Error is returned.
    """
    if len(confidences) != len(accuracies):
        raise ValueError("confidences and accuracies must have same length")
    if not confidences:
        return 0.0

    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    ece = 0.0
    total = len(confidences)

    for i in range(n_bins):
        lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
        bin_confidences = [c for c in confidences if lo <= c < hi or (i == n_bins - 1 and c == hi)]
        bin_accuracies = [a for c, a in zip(confidences, accuracies) if lo <= c < hi or (i == n_bins - 1 and c == hi)]

        if bin_confidences:
            avg_conf = sum(bin_confidences) / len(bin_confidences)
            avg_acc = sum(bin_accuracies) / len(bin_accuracies)
            ece += (len(bin_confidences) / total) * abs(avg_conf - avg_acc)

    return ece


def compute_resignation_rate(evaluations: list[dict]) -> float:
    """Given a list of evaluations, When resignation is detected, Then the resignation rate is returned."""
    if not evaluations:
        return 0.0
    resigned = sum(1 for e in evaluations if e.get("resigned", False))
    return resigned / len(evaluations)


def compute_gambling_tendency(evaluations: list[dict]) -> float:
    """Given a list of evaluations, When gambling behavior is detected, Then the gambling tendency is returned."""
    if not evaluations:
        return 0.0
    gambled = sum(1 for e in evaluations if e.get("gambled", False))
    return gambled / len(evaluations)


class TestMetricsGivenWhenThen:
    """
    Given SF labels and LLM assessments are paired in the evaluation DB,
    When the metrics engine computes calibration,
    Then ECE (Expected Calibration Error), resignation rate, and gambling tendency are output.
    """

    def test_all_draw_dataset_produces_ece_near_zero(self):
        """Given all-draw dataset (50% confidence, 50% accuracy), When ECE is computed, Then ECE should be near 0."""
        confidences = [0.5] * 100
        accuracies = [True, False] * 50  # 50% accuracy
        ece = compute_ece(confidences, accuracies)
        assert ece < 0.05, f"All-draw ECE should be near 0, got {ece}"

    def test_forced_win_dataset_produces_high_resignation(self):
        """Given a forced-win dataset, When resignation is computed, Then resignation rate should be > 0.8."""
        evaluations = [{"resigned": True} for _ in range(90)] + [{"resigned": False} for _ in range(10)]
        rate = compute_resignation_rate(evaluations)
        assert rate > 0.8, f"Forced-win resignation rate should be > 0.8, got {rate}"

    def test_no_resignation_for_draw_dataset(self):
        """Given all-draw evaluations, When resignation is computed, Then rate should be 0."""
        evaluations = [{"resigned": False} for _ in range(50)]
        rate = compute_resignation_rate(evaluations)
        assert rate == 0.0, f"All-draw resignation rate should be 0, got {rate}"

    def test_ece_handles_empty_input(self):
        """Given empty lists, When ECE is computed, Then return 0.0."""
        ece = compute_ece([], [])
        assert ece == 0.0, f"Empty input ECE should be 0.0, got {ece}"

    def test_gambling_tendency_zero(self):
        """Given no gambling evaluations, When gambling tendency is computed, Then return 0.0."""
        evaluations = [{"gambled": False} for _ in range(50)]
        tendency = compute_gambling_tendency(evaluations)
        assert tendency == 0.0, f"No gambling tendency should be 0.0, got {tendency}"

    def test_gambling_tendency_high(self):
        """Given 80% gambled evaluations, When gambling tendency is computed, Then return 0.8."""
        evaluations = [{"gambled": True} for _ in range(80)] + [{"gambled": False} for _ in range(20)]
        tendency = compute_gambling_tendency(evaluations)
        assert abs(tendency - 0.8) < 0.01, f"Gambling tendency should be ~0.8, got {tendency}"

    def test_ece_perfect_calibration(self):
        """Given perfectly calibrated predictions (all within same bin), When ECE is computed, Then ECE should be near 0."""
        # Perfect calibration: all confidences in same bin match accuracy exactly
        confidences = [0.8] * 100  # all in bin 8
        accuracies = [True] * 80 + [False] * 20  # exactly 80% accuracy = confidence
        ece = compute_ece(confidences, accuracies)
        assert ece < 0.01, f"Perfect calibration ECE should be near 0, got {ece}"
