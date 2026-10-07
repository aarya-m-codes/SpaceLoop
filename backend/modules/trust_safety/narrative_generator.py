"""Forensic Narrative Generator for SpaceLoop Trust & Safety Engine (System A).

Produces human-readable, auditable forensic investigation reports.
Implements 3-tier fallback architecture:
1. Primary: Groq API (LLaMA 3.3 70B)
2. Fallback: Google Gemini API (gemini-2.5-flash)
3. Final Fallback: Deterministic Rule-Based Forensic Explanation Engine
"""

import json
import logging
import os
from typing import Any

from backend.modules.trust_safety.signals import BehavioralSignal

logger = logging.getLogger("spaceloop.trust_safety.narrative")


class ForensicNarrativeGenerator:
    """Generates explainable Trust & Safety forensic narratives across AI and deterministic tiers."""

    @classmethod
    def generate(
        cls,
        entity_type: str,
        entity_id: str | int,
        signals: list[BehavioralSignal],
        graph_summary: dict[str, Any],
        risk_score: float,
        action: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Execute resilient narrative generation pipeline."""
        meta = metadata or {}
        groq_api_key = os.getenv("GROQ_API_KEY")
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        # 1. Primary: Groq
        if groq_api_key and not os.getenv("SIMULATE_AI_OUTAGE"):
            try:
                narrative = cls._call_groq(
                    api_key=groq_api_key,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    signals=signals,
                    graph_summary=graph_summary,
                    risk_score=risk_score,
                    action=action,
                    metadata=meta,
                )
                if narrative:
                    logger.info("Forensic narrative generated via Groq.")
                    return narrative
            except Exception as e:
                logger.warning(f"Groq narrative generation failed ({e}), falling back to Gemini.")

        # 2. Fallback: Google Gemini
        if gemini_api_key and not os.getenv("SIMULATE_AI_OUTAGE"):
            try:
                narrative = cls._call_gemini(
                    api_key=gemini_api_key,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    signals=signals,
                    graph_summary=graph_summary,
                    risk_score=risk_score,
                    action=action,
                    metadata=meta,
                )
                if narrative:
                    logger.info("Forensic narrative generated via Gemini.")
                    return narrative
            except Exception as e:
                logger.warning(f"Gemini narrative generation failed ({e}), falling back to deterministic.")

        # 3. Final Fallback: Deterministic rule-based forensic explanation
        logger.debug("Generating deterministic rule-based forensic narrative.")
        return cls._generate_deterministic(
            entity_type=entity_type,
            entity_id=entity_id,
            signals=signals,
            graph_summary=graph_summary,
            risk_score=risk_score,
            action=action,
            metadata=meta,
        )

    # -------------------------------------------------------------------------
    # Tier 1: Groq
    # -------------------------------------------------------------------------
    @classmethod
    def _call_groq(
        cls,
        api_key: str,
        entity_type: str,
        entity_id: str | int,
        signals: list[BehavioralSignal],
        graph_summary: dict[str, Any],
        risk_score: float,
        action: str,
        metadata: dict[str, Any],
    ) -> str | None:
        import groq
        client = groq.Groq(api_key=api_key, timeout=3.0)

        prompt = cls._build_prompt(entity_type, entity_id, signals, graph_summary, risk_score, action, metadata)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Lead Trust & Safety Investigator for SpaceLoop, an Indian physical space marketplace. "
                        "Produce a rigorous, objective, professional forensic investigative report in markdown explaining "
                        "the risk assessment, evidentiary graph findings, and recommended action. Be concise, direct, and fact-based."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=600,
        )

        if completion and completion.choices:
            return completion.choices[0].message.content.strip()
        return None

    # -------------------------------------------------------------------------
    # Tier 2: Gemini
    # -------------------------------------------------------------------------
    @classmethod
    def _call_gemini(
        cls,
        api_key: str,
        entity_type: str,
        entity_id: str | int,
        signals: list[BehavioralSignal],
        graph_summary: dict[str, Any],
        risk_score: float,
        action: str,
        metadata: dict[str, Any],
    ) -> str | None:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt = cls._build_prompt(entity_type, entity_id, signals, graph_summary, risk_score, action, metadata)
        system_instruction = (
            "You are the Lead Trust & Safety Investigator for SpaceLoop. "
            "Write a clear, factual, bulleted forensic audit report detailing why this entity was assigned this risk score and action."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instruction}\n\n{prompt}",
        )

        if response and response.text:
            return response.text.strip()
        return None

    # -------------------------------------------------------------------------
    # Tier 3: Deterministic Rule-Based Forensic Explanation
    # -------------------------------------------------------------------------
    @classmethod
    def _generate_deterministic(
        cls,
        entity_type: str,
        entity_id: str | int,
        signals: list[BehavioralSignal],
        graph_summary: dict[str, Any],
        risk_score: float,
        action: str,
        metadata: dict[str, Any],
    ) -> str:
        lines: list[str] = []

        # Executive Header
        lines.append(f"### SpaceLoop Trust & Safety Forensic Audit: {entity_type.upper()} #{entity_id}")
        lines.append(f"- **Calculated Risk Score**: `{round(risk_score, 3)}` / 1.000")
        lines.append(f"- **Recommended Disposition**: **{action.upper()}**")
        lines.append(f"- **Signals Identified**: `{len(signals)}` active behavioral triggers")
        lines.append("")

        # Section 1: Findings Breakdown
        if signals:
            lines.append("#### Behavioral Threat Signals")
            for sig in signals:
                lines.append(f"- **[{sig.severity}] {sig.signal_type}: {sig.title}** (Weight: {round(sig.weight, 2)})")
                lines.append(f"  - *Context*: {sig.description}")
                for ev in sig.evidence:
                    lines.append(f"  - *Evidence*: {ev}")
            lines.append("")
        else:
            lines.append("#### Behavioral Threat Signals")
            lines.append("- No adverse behavioral signals detected across transaction history and session logs.")
            lines.append("")

        # Section 2: Graph Topology
        lines.append("#### Graph Relationship & Topology Analysis")
        has_cycles = graph_summary.get("has_cycles", False)
        has_device_clustering = graph_summary.get("has_device_clustering", False)
        cycles = graph_summary.get("cycles", [])
        clusters = graph_summary.get("clusters", [])

        if has_cycles:
            lines.append(f"- **Circular Collusion Detected**: Found {len(cycles)} closed transaction loop(s).")
            for c in cycles[:3]:
                lines.append(f"  - Loop: `{c.get('description')}` ({c.get('cycle_type')})")
        else:
            lines.append("- **Circular Transaction Cycles**: None detected.")

        if has_device_clustering:
            lines.append(f"- **Hardware/Device Multiplexing**: Found {len(clusters)} shared device cluster(s).")
            for cl in clusters[:3]:
                lines.append(f"  - Device `{cl.get('fingerprint')[:16]}...` shared across accounts: {cl.get('user_ids')}")
        else:
            lines.append("- **Hardware/Device Multiplexing**: No anomalous device sharing identified.")
        lines.append("")

        # Section 3: Administrative Recommendation
        lines.append("#### Investigator Assessment & Recommended Enforcement")
        if action == "BLOCK":
            lines.append(
                "Critical safety violation detected with verified policy non-compliance. "
                "Immediate administrative suspension or transaction freeze is required to protect escrow funds."
            )
        elif action in ("HOLD", "REVIEW"):
            lines.append(
                "Moderate-to-high risk anomalies observed. Account flagged for human Trust & Safety compliance review. "
                "Escrow payout should remain held pending secondary document verification."
            )
        elif action in ("CHALLENGE", "MFA", "KYC"):
            lines.append(
                "Anomalous telemetry detected requiring step-up authentication. User should be prompted for "
                "mandatory government KYC verification or two-factor authentication challenge."
            )
        else:
            lines.append("Entity exhibits normal marketplace behavior consistent with verified peer-to-peer norms. Allow operation.")

        return "\n".join(lines)

    @classmethod
    def _build_prompt(
        cls,
        entity_type: str,
        entity_id: str | int,
        signals: list[BehavioralSignal],
        graph_summary: dict[str, Any],
        risk_score: float,
        action: str,
        metadata: dict[str, Any],
    ) -> str:
        signal_details = [
            {"type": s.signal_type, "severity": s.severity, "weight": s.weight, "evidence": s.evidence}
            for s in signals
        ]
        return (
            f"Generate a Trust & Safety forensic investigative narrative for:\n"
            f"Target: {entity_type} #{entity_id}\n"
            f"Risk Score: {risk_score}\n"
            f"Action: {action}\n"
            f"Signals: {json.dumps(signal_details, indent=2)}\n"
            f"Graph Summary: {json.dumps(graph_summary, indent=2)}\n"
            f"Metadata: {json.dumps(metadata, indent=2)}\n"
        )
