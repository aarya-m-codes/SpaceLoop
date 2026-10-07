"""Trust & Safety Service Orchestrator (System A).

Coordinates:
- Behavioral Signal Extraction
- Multi-partite Graph Subgraph & Cycle Analytics
- Composite Risk Decisioning
- Forensic Narrative Generation (Groq -> Gemini -> Deterministic)
- Audit trail & RiskAssessment persistence
"""

from datetime import datetime, timezone
import logging
from typing import Any

from backend.core.database import db
from backend.modules.trust_safety.graph_analyzer import GraphAnalyzer
from backend.modules.trust_safety.narrative_generator import ForensicNarrativeGenerator
from backend.modules.trust_safety.signals import SignalExtractor
from models import Booking, FraudAlertRecord, RiskAssessment, Space, User

logger = logging.getLogger("spaceloop.trust_safety.service")


class TrustSafetyService:
    """Enterprise Trust & Safety evaluation orchestrator."""

    @classmethod
    def evaluate_entity(
        cls,
        entity_type: str,
        entity_id: str | int,
        context: dict[str, Any] | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run complete Trust & Safety forensic audit on a target entity."""
        ctx = context or {}
        norm_type = entity_type.upper().strip()

        # Resolve primary entity
        user = None
        space = None
        booking = None

        if norm_type in ("USER", "SEEKER", "HOST"):
            user = User.query.get(int(entity_id))
            if not user:
                raise ValueError(f"User with ID {entity_id} not found.")
        elif norm_type == "SPACE":
            space = Space.query.get(int(entity_id))
            if not space:
                raise ValueError(f"Space with ID {entity_id} not found.")
            user = space.host
        elif norm_type == "BOOKING":
            booking = Booking.query.get(int(entity_id))
            if not booking:
                raise ValueError(f"Booking with ID {entity_id} not found.")
            user = booking.guest
            space = booking.space
        elif norm_type in ("DEVICE", "IP"):
            # Device or IP evaluation
            pass
        else:
            raise ValueError(f"Unsupported entity_type: '{entity_type}'. Must be USER, SPACE, BOOKING, DEVICE, or IP.")

        # 1. Extract Behavioral Signals
        signals = SignalExtractor.extract_all(
            user=user,
            space=space,
            booking=booking,
            device_fingerprint=ctx.get("device_fingerprint"),
            ip_address=ctx.get("ip_address"),
            context=ctx,
        )

        # 2. Build multi-partite subgraph and detect cycles
        subgraph = GraphAnalyzer.build_subgraph(
            entity_type=norm_type,
            entity_id=entity_id,
            max_depth=2,
        )

        cycles = subgraph.get("cycles", [])
        clusters = subgraph.get("clusters", [])

        # 3. Calculate composite risk score
        # Base risk from signals
        signal_weights = [s.weight for s in signals]
        if signal_weights:
            max_signal_weight = max(signal_weights)
            avg_signal_weight = sum(signal_weights) / len(signal_weights)
            # 70% max signal + 30% aggregate
            base_risk = 0.70 * max_signal_weight + 0.30 * min(1.0, avg_signal_weight * 1.2)
        else:
            base_risk = 0.05

        # Factor in graph topological threats
        if cycles:
            base_risk = max(base_risk, 0.85)
        if clusters:
            base_risk = max(base_risk, 0.65)

        risk_score = round(min(1.0, max(0.0, base_risk)), 3)

        # Determine risk level
        if risk_score >= 0.80:
            risk_level = "CRITICAL"
        elif risk_score >= 0.60:
            risk_level = "HIGH"
        elif risk_score >= 0.40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Determine action
        if risk_score >= 0.80:
            action = "BLOCK"
        elif risk_score >= 0.60:
            action = "REVIEW"
        elif risk_score >= 0.40:
            action = "CHALLENGE"
        else:
            action = "ALLOW"

        # 4. Generate forensic narrative
        graph_summary = {
            "has_cycles": len(cycles) > 0,
            "cycles": cycles,
            "has_device_clustering": len(clusters) > 0,
            "clusters": clusters,
            "total_nodes": len(subgraph.get("nodes", [])),
            "total_edges": len(subgraph.get("edges", [])),
        }

        narrative = ForensicNarrativeGenerator.generate(
            entity_type=norm_type,
            entity_id=entity_id,
            signals=signals,
            graph_summary=graph_summary,
            risk_score=risk_score,
            action=action,
            metadata=ctx,
        )

        assessment_id = None
        if persist:
            # Associate user ID
            target_user_id = user.id if user else 1
            assessment = RiskAssessment(
                user_id=target_user_id,
                booking_id=booking.id if booking else None,
                entity_type=norm_type,
                entity_id=str(entity_id),
                risk_score=risk_score,
                risk_level=risk_level,
                evaluated_rules=[s.signal_type for s in signals],
                signals=[s.to_dict() for s in signals],
                narrative=narrative,
                action_taken=action,
            )
            db.session.add(assessment)

            # If BLOCK or REVIEW, log alert for compliance dashboard
            if action in ("BLOCK", "REVIEW"):
                alert = FraudAlertRecord(
                    user_id=target_user_id,
                    title=f"Trust & Safety Alert: {norm_type} #{entity_id} [{action}]",
                    details={
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "action": action,
                        "signals": [s.signal_type for s in signals],
                        "has_cycles": len(cycles) > 0,
                    },
                    status="OPEN",
                )
                db.session.add(alert)

            db.session.commit()
            assessment_id = assessment.id

        return {
            "assessment_id": assessment_id,
            "entity_type": norm_type,
            "entity_id": str(entity_id),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "action": action,
            "signals": [s.to_dict() for s in signals],
            "graph": subgraph,
            "narrative": narrative,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_assessments(
        cls,
        limit: int = 50,
        offset: int = 0,
        risk_level: str | None = None,
        action: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve historical risk assessments with administrative filtering."""
        query = RiskAssessment.query

        if risk_level:
            query = query.filter_by(risk_level=risk_level.upper())
        if action:
            query = query.filter_by(action_taken=action.upper())

        assessments = (
            query.order_by(RiskAssessment.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [a.to_dict() for a in assessments]

    @classmethod
    def get_graph(cls, entity_type: str, entity_id: str | int) -> dict[str, Any]:
        """Fetch topological entity relationship graph."""
        return GraphAnalyzer.build_subgraph(entity_type=entity_type, entity_id=entity_id)
