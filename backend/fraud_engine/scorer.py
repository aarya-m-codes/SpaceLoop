"""Autonomous ML Risk Scorer & Governance Engine (System B).

Enforces:
1. Strict Decision Thresholds:
   - risk >= 0.80 => BLOCK
   - risk >= 0.60 => HOLD / REVIEW
   - risk >= 0.40 => CHALLENGE / MFA / KYC
   - risk < 0.40  => ALLOW
2. Critical Safety Invariant:
   Users are NEVER automatically blocked solely because an ML model produced an anomaly score
   without deterministic policy validation. If ML anomaly is high but uncorroborated by policy rules,
   risk is capped below 0.80 and routed to HOLD / REVIEW.
3. 100% Explainability for every scoring decision.
"""

import logging
from typing import Any

from fraud_engine.feature_extractor import FeatureExtractor
from fraud_engine.isolation_forest import IsolationForestAnomalyDetector
from fraud_engine.rules import DeterministicRule, PolicyRuleEngine

logger = logging.getLogger("spaceloop.fraud.scorer")


class FraudRiskScorer:
    """Evaluates composite transaction risk and executes safe policy governance."""

    # Explicit threshold boundaries
    THRESHOLD_BLOCK = 0.80
    THRESHOLD_REVIEW = 0.60
    THRESHOLD_CHALLENGE = 0.40

    @classmethod
    def evaluate(
        cls,
        features_dict: dict[str, Any],
        vector: list[float],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute composite risk score, apply governance caps, and format explanation."""
        ctx = context or {}

        # 1. Evaluate ML Anomaly Model
        ml_result = IsolationForestAnomalyDetector.score(vector)
        ml_anomaly_score = ml_result["anomaly_score"]
        engine_mode = ml_result["engine_mode"]

        # 2. Evaluate Deterministic Policy Rules
        triggered_rules: list[DeterministicRule] = PolicyRuleEngine.evaluate(features_dict, ctx)
        rule_score = 0.0
        if triggered_rules:
            # Take highest policy rule severity as baseline
            rule_weights = [r.weight for r in triggered_rules]
            max_rule_weight = max(rule_weights)
            rule_score = max_rule_weight

        # 3. Compute Composite Raw Risk
        if triggered_rules:
            # 60% rule authority, 40% ML behavioral anomaly
            raw_risk = 0.60 * rule_score + 0.40 * ml_anomaly_score
            # If critical rule fired (weight >= 0.85), raw risk must be at least rule_score
            if rule_score >= 0.85:
                raw_risk = max(raw_risk, rule_score)
        else:
            # ML-only signal
            raw_risk = ml_anomaly_score

        raw_risk = round(min(1.0, max(0.0, raw_risk)), 3)

        # 4. Critical Safety Governance: Prevent ML-only Auto-Ban
        is_governance_capped = False
        governance_reason = None
        final_risk = raw_risk

        has_authoritative_rule = any(r.weight >= 0.75 for r in triggered_rules)

        if final_risk >= cls.THRESHOLD_BLOCK and not has_authoritative_rule:
            # ML produced a high anomaly score, but no deterministic policy rule validates BLOCK.
            final_risk = 0.75  # Cap below 0.80 so it routes to HOLD / REVIEW
            is_governance_capped = True
            governance_reason = (
                "Automatic account block suppressed: ML anomaly score was >= 0.80, but no "
                "authoritative deterministic policy rule validated an immediate block. "
                "Routing to HOLD / REVIEW for human investigator audit."
            )

        # 5. Determine Disposition
        if final_risk >= cls.THRESHOLD_BLOCK:
            decision = "BLOCK"
            disposition = "BLOCK"
            requires_action = "IMMEDIATE_ACCOUNT_AND_ESCROW_FREEZE"
        elif final_risk >= cls.THRESHOLD_REVIEW:
            decision = "HOLD / REVIEW"
            disposition = "REVIEW"
            requires_action = "MANUAL_COMPLIANCE_INVESTIGATION"
        elif final_risk >= cls.THRESHOLD_CHALLENGE:
            decision = "CHALLENGE / MFA / KYC"
            disposition = "CHALLENGE"
            requires_action = "STEP_UP_AUTHENTICATION_OR_KYC"
        else:
            decision = "ALLOW"
            disposition = "ALLOW"
            requires_action = "STANDARD_PROCESSING"

        # 6. Build Explainable Narrative
        explanation_lines = [
            f"Risk Score: {final_risk:.3f} | Decision: {decision}",
            f"ML Anomaly Score: {ml_anomaly_score:.3f} (Engine: {engine_mode})",
            f"Deterministic Policy Rules Triggered: {len(triggered_rules)}",
        ]
        if triggered_rules:
            explanation_lines.append("Triggered Rules:")
            for r in triggered_rules:
                explanation_lines.append(f"  - [{r.severity}] {r.code}: {r.description} (weight={r.weight})")
        else:
            explanation_lines.append("Triggered Rules: None (0 policy violations)")

        if is_governance_capped:
            explanation_lines.append(f"Safety Governance Note: {governance_reason}")

        explanation = "\n".join(explanation_lines)

        return {
            "risk_score": final_risk,
            "raw_risk_score": raw_risk,
            "decision": decision,
            "disposition": disposition,
            "threshold_applied": (
                ">= 0.80 (BLOCK)" if final_risk >= cls.THRESHOLD_BLOCK else
                ">= 0.60 (HOLD / REVIEW)" if final_risk >= cls.THRESHOLD_REVIEW else
                ">= 0.40 (CHALLENGE / MFA / KYC)" if final_risk >= cls.THRESHOLD_CHALLENGE else
                "< 0.40 (ALLOW)"
            ),
            "ml_anomaly_score": ml_anomaly_score,
            "engine_mode": engine_mode,
            "rule_score": rule_score,
            "triggered_rules": [r.to_dict() for r in triggered_rules],
            "governance_capped": is_governance_capped,
            "governance_reason": governance_reason,
            "requires_action": requires_action,
            "features": features_dict,
            "explanation": explanation,
        }
