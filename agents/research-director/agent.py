from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Sequence

from agent_engine import compare_payloads, rank_multibagger_candidates
from mcp_server import API_BASE, api_get, fetch_many, normalize_symbols


@dataclass(frozen=True)
class ResearchAgentConfig:
    batch_size: int = 250
    max_symbols: int = 1000
    shortlist_per_batch: int = 12
    default_top_k: int = 20
    default_deep_diligence_k: int = 10
    min_evidence_completeness: float = 60.0

    def validate(self) -> None:
        if not 1 <= self.batch_size <= self.max_symbols:
            raise ValueError("batch_size must be between 1 and max_symbols")
        if not 1 <= self.shortlist_per_batch <= 100:
            raise ValueError("shortlist_per_batch must be between 1 and 100")
        if not 1 <= self.default_top_k <= 100:
            raise ValueError("default_top_k must be between 1 and 100")
        if not 1 <= self.default_deep_diligence_k <= self.default_top_k:
            raise ValueError("default_deep_diligence_k must be <= default_top_k")


class ResearchDirector:
    """Deterministic orchestration layer over the ASET SignalDesk research API."""

    def __init__(self, config: ResearchAgentConfig | None = None) -> None:
        self.config = config or ResearchAgentConfig()
        self.config.validate()

    async def preflight(self) -> dict[str, Any]:
        failures: list[str] = []
        try:
            health = await api_get("/health")
        except Exception as exc:
            health = {"status": "error"}
            failures.append(f"health check failed: {exc}")
        try:
            config = await api_get("/api/v1/config")
        except Exception as exc:
            config = {"status": "error"}
            failures.append(f"configuration check failed: {exc}")
        return {
            "api_base": API_BASE,
            "healthy": not failures,
            "health": health,
            "config": config,
            "failures": failures,
        }

    def _partition(self, symbols: Sequence[str]) -> list[list[str]]:
        return [list(symbols[i:i + self.config.batch_size]) for i in range(0, len(symbols), self.config.batch_size)]

    @staticmethod
    def _candidate_key(row: dict[str, Any]) -> str:
        return str(row.get("symbol") or "").upper()

    def _merge_candidates(self, batches: Sequence[Sequence[dict[str, Any]]], top_k: int) -> list[dict[str, Any]]:
        best_by_symbol: dict[str, dict[str, Any]] = {}
        for batch in batches:
            for candidate in batch:
                symbol = self._candidate_key(candidate)
                if not symbol:
                    continue
                previous = best_by_symbol.get(symbol)
                if previous is None or float(candidate.get("score") or 0) > float(previous.get("score") or 0):
                    best_by_symbol[symbol] = candidate
        merged = sorted(
            best_by_symbol.values(),
            key=lambda row: (-float(row.get("score") or 0), self._candidate_key(row)),
        )
        return merged[:top_k]

    def _apply_evidence_gate(self, candidates: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for candidate in candidates:
            completeness = float((candidate.get("signals") or {}).get("evidence_completeness") or 0)
            copy = dict(candidate)
            if completeness < self.config.min_evidence_completeness:
                copy["status"] = "evidence gap"
                risks = list(copy.get("risk_flags") or [])
                message = f"evidence completeness below {self.config.min_evidence_completeness:.0f}%"
                if message not in risks:
                    risks.append(message)
                copy["risk_flags"] = risks
                rejected.append(copy)
            else:
                accepted.append(copy)
        return accepted, rejected

    async def run(
        self,
        symbols: Sequence[str],
        *,
        top_k: int | None = None,
        deep_diligence_k: int | None = None,
        entitlement: str = "",
        objective: str = "Find research-worthy multi-year compounding candidates",
    ) -> dict[str, Any]:
        self.config.validate()
        if entitlement not in ("", "realtime", "delayed"):
            raise ValueError("entitlement must be empty, realtime, or delayed")

        requested_top_k = max(1, min(int(top_k or self.config.default_top_k), 100))
        requested_deep_k = max(1, min(int(deep_diligence_k or self.config.default_deep_diligence_k), requested_top_k))

        clean = normalize_symbols(list(symbols))
        if len(clean) > self.config.max_symbols:
            raise ValueError(f"symbols exceeds ResearchDirector max_symbols={self.config.max_symbols}")

        run_id = f"aset-{uuid.uuid4().hex[:12]}"
        stages: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []

        preflight = await self.preflight()
        stages.append({
            "name": "preflight",
            "status": "ok" if preflight["healthy"] else "degraded",
            "details": preflight,
        })

        batches = self._partition(clean)
        batch_candidates: list[list[dict[str, Any]]] = []

        for index, batch in enumerate(batches, start=1):
            rows, batch_failures = await fetch_many(batch, entitlement)
            failures.extend({"batch": index, **failure} for failure in batch_failures)
            candidates = rank_multibagger_candidates(rows, top_k=self.config.shortlist_per_batch)
            batch_candidates.append(candidates)
            stages.append({
                "name": "quant_screen",
                "batch": index,
                "requested": len(batch),
                "analyzed": len(rows),
                "failed": len(batch_failures),
                "status": "ok" if rows else "failed",
            })

        merged = self._merge_candidates(batch_candidates, requested_top_k)
        stages.append({
            "name": "merge_and_deduplicate",
            "status": "ok",
            "input_batches": len(batch_candidates),
            "shortlist_size": len(merged),
        })

        shortlist_symbols = [self._candidate_key(row) for row in merged if self._candidate_key(row)]
        comparison: list[dict[str, Any]] = []
        if shortlist_symbols:
            compare_rows, compare_failures = await fetch_many(shortlist_symbols[:100], entitlement)
            comparison = compare_payloads(compare_rows)
            failures.extend({"stage": "compare", **failure} for failure in compare_failures)

        stages.append({
            "name": "normalized_compare",
            "status": "ok" if comparison else "degraded",
            "compared": len(comparison),
        })

        evidence_pass, evidence_reject = self._apply_evidence_gate(merged)
        stages.append({
            "name": "evidence_gate",
            "status": "ok",
            "accepted": len(evidence_pass),
            "rejected": len(evidence_reject),
            "minimum_evidence_completeness": self.config.min_evidence_completeness,
        })

        queue = evidence_pass[:requested_deep_k]
        data_gaps = sorted({
            risk
            for candidate in merged
            for risk in (candidate.get("risk_flags") or [])
            if "unavailable" in str(risk).lower()
            or "meaningful" in str(risk).lower()
            or "evidence" in str(risk).lower()
        })

        analyzed = sum(int(stage.get("analyzed") or 0) for stage in stages if stage.get("name") == "quant_screen")
        return {
            "run_id": run_id,
            "objective": objective,
            "agent": "ASET Research Director",
            "execution_policy": "read-only research; no brokerage execution",
            "preflight": preflight,
            "universe": {
                "requested": len(clean),
                "batch_count": len(batches),
                "batch_size": self.config.batch_size,
                "analyzed": analyzed,
                "failed": len(failures),
            },
            "stages": stages,
            "shortlist": merged,
            "comparison": comparison,
            "deep_diligence_queue": queue,
            "evidence_rejections": evidence_reject,
            "data_gaps": data_gaps,
            "failures": failures,
            "research_rules": [
                "Provider-returned values are preserved; missing values are never imputed.",
                "Screen scores are prioritization aids, not intrinsic-value models.",
                "Material business claims require primary-source verification.",
                "Bull and skeptic cases must be evaluated independently for advanced candidates.",
                "A research candidate is not an instruction to buy, sell, or trade.",
            ],
        }


async def run_research_director(
    symbols: Sequence[str],
    *,
    top_k: int = 20,
    deep_diligence_k: int = 10,
    entitlement: str = "",
) -> dict[str, Any]:
    return await ResearchDirector().run(
        symbols,
        top_k=top_k,
        deep_diligence_k=deep_diligence_k,
        entitlement=entitlement,
    )
