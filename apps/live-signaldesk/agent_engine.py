"""Compatibility wrapper for the shared ASET multibagger scoring engine."""

from stock_analyzer.multibagger_scoring import (
    compare_payloads,
    rank_multibagger_candidates,
    score_candidate,
)

__all__ = ["compare_payloads", "rank_multibagger_candidates", "score_candidate"]
