"""Multi-partite Graph Relationship Analyzer for SpaceLoop Trust & Safety Engine (System A).

Constructs topological entity graphs across:
- Users
- Spaces
- Devices
- IP Addresses
- Bookings

Features:
- Extracts bi-directional subgraphs centered on any entity (User, Space, Device, IP, Booking)
- Identifies suspicious circular transactions ($A \to B \to A$, $A \to B \to C \to A$)
- Detects multi-account hardware clustering (shared device fingerprints across accounts)
"""

from collections import defaultdict
from datetime import datetime, timezone
import logging
from typing import Any

from backend.core.database import db
from models import Booking, DeviceSession, FraudEventRecord, Space, User

logger = logging.getLogger("spaceloop.trust_safety.graph")


class GraphNode:
    """Graph node representing an entity in the marketplace ecosystem."""

    def __init__(self, node_id: str, node_type: str, label: str, metadata: dict[str, Any] | None = None):
        self.node_id = node_id        # e.g., 'user:1', 'space:42', 'device:abc-123'
        self.node_type = node_type    # 'USER', 'SPACE', 'DEVICE', 'IP', 'BOOKING'
        self.label = label
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "type": self.node_type,
            "label": self.label,
            "metadata": self.metadata,
        }


class GraphEdge:
    """Directed edge representing a behavioral or transactional relationship."""

    def __init__(self, source_id: str, target_id: str, relation: str, weight: float = 1.0, metadata: dict[str, Any] | None = None):
        self.source_id = source_id
        self.target_id = target_id
        self.relation = relation      # OWNS, RESERVES, BOOKED_BY, USED_DEVICE, USED_IP, TRANSACTED_WITH
        self.weight = weight
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation,
            "weight": self.weight,
            "metadata": self.metadata,
        }


class GraphAnalyzer:
    """Engine for exploring multi-partite relationships and detecting circular cycles."""

    @classmethod
    def build_subgraph(
        cls,
        entity_type: str,
        entity_id: str | int,
        max_depth: int = 2,
    ) -> dict[str, Any]:
        """Construct multi-partite subgraph centered on the target entity."""
        norm_type = entity_type.upper().strip()
        target_root_id = f"{norm_type.lower()}:{entity_id}"

        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        visited: set[str] = set()

        # Seed root node
        cls._add_entity_node(norm_type, str(entity_id), nodes)

        # Traverse connections
        if norm_type in ("USER", "SEEKER", "HOST"):
            cls._expand_user(int(entity_id), nodes, edges, max_depth)
        elif norm_type == "SPACE":
            cls._expand_space(int(entity_id), nodes, edges, max_depth)
        elif norm_type == "BOOKING":
            cls._expand_booking(int(entity_id), nodes, edges, max_depth)
        elif norm_type == "DEVICE":
            cls._expand_device(str(entity_id), nodes, edges, max_depth)
        elif norm_type == "IP":
            cls._expand_ip(str(entity_id), nodes, edges, max_depth)

        # Run cycle detection on user-to-user transaction projection
        cycles = cls.detect_user_cycles(nodes)
        clusters = cls.detect_device_clusters(nodes)

        return {
            "root_id": target_root_id,
            "entity_type": norm_type,
            "entity_id": str(entity_id),
            "nodes": [n.to_dict() for n in nodes.values()],
            "edges": [e.to_dict() for e in edges],
            "cycles": cycles,
            "clusters": clusters,
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "has_cycles": len(cycles) > 0,
                "has_device_clustering": len(clusters) > 0,
            },
        }

    # -------------------------------------------------------------------------
    # Expansion Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _add_entity_node(cls, entity_type: str, raw_id: str, nodes: dict[str, GraphNode]) -> None:
        key = f"{entity_type.lower()}:{raw_id}"
        if key in nodes:
            return

        if entity_type == "USER":
            try:
                user = db.session.get(User, int(raw_id))
                if user:
                    nodes[key] = GraphNode(
                        node_id=key,
                        node_type="USER",
                        label=f"{user.full_name} ({user.role})",
                        metadata={"email": user.email, "trust_score": user.trust_score, "is_verified": user.is_verified},
                    )
            except Exception:
                pass
        elif entity_type == "SPACE":
            try:
                space = db.session.get(Space, int(raw_id))
                if space:
                    nodes[key] = GraphNode(
                        node_id=key,
                        node_type="SPACE",
                        label=f"{space.title} ({space.city})",
                        metadata={"host_id": space.host_id, "price": space.price_per_hour, "city": space.city},
                    )
            except Exception:
                pass
        elif entity_type == "BOOKING":
            try:
                booking = db.session.get(Booking, int(raw_id))
                if booking:
                    nodes[key] = GraphNode(
                        node_id=key,
                        node_type="BOOKING",
                        label=f"Booking #{booking.id} ({booking.status})",
                        metadata={"guest_id": booking.guest_id, "space_id": booking.space_id, "status": booking.status},
                    )
            except Exception:
                pass
        elif entity_type == "DEVICE":
            nodes[key] = GraphNode(
                node_id=key,
                node_type="DEVICE",
                label=f"Device {raw_id[:12]}...",
                metadata={"fingerprint": raw_id},
            )
        elif entity_type == "IP":
            nodes[key] = GraphNode(
                node_id=key,
                node_type="IP",
                label=f"IP {raw_id}",
                metadata={"ip_address": raw_id},
            )

    @classmethod
    def _expand_user(cls, user_id: int, nodes: dict[str, GraphNode], edges: list[GraphEdge], depth: int) -> None:
        user_key = f"user:{user_id}"

        # 1. Spaces owned by this user
        spaces = Space.query.filter_by(host_id=user_id).all()
        for s in spaces:
            space_key = f"space:{s.id}"
            cls._add_entity_node("SPACE", str(s.id), nodes)
            edges.append(GraphEdge(user_key, space_key, "OWNS"))

            # Bookings on this space
            bookings_on_space = Booking.query.filter_by(space_id=s.id).limit(20).all()
            for b in bookings_on_space:
                b_key = f"booking:{b.id}"
                cls._add_entity_node("BOOKING", str(b.id), nodes)
                edges.append(GraphEdge(b_key, space_key, "RESERVES"))

                # Guest who made booking
                guest_key = f"user:{b.guest_id}"
                cls._add_entity_node("USER", str(b.guest_id), nodes)
                edges.append(GraphEdge(guest_key, b_key, "BOOKED"))
                edges.append(GraphEdge(guest_key, user_key, "TRANSACTED_WITH", metadata={"booking_id": b.id}))

        # 2. Bookings created by this user
        guest_bookings = Booking.query.filter_by(guest_id=user_id).limit(20).all()
        for b in guest_bookings:
            b_key = f"booking:{b.id}"
            cls._add_entity_node("BOOKING", str(b.id), nodes)
            edges.append(GraphEdge(user_key, b_key, "BOOKED"))

            sp = b.space or db.session.get(Space, b.space_id)
            if sp:
                space_key = f"space:{sp.id}"
                cls._add_entity_node("SPACE", str(sp.id), nodes)
                edges.append(GraphEdge(b_key, space_key, "RESERVES"))

                host_key = f"user:{sp.host_id}"
                cls._add_entity_node("USER", str(sp.host_id), nodes)
                edges.append(GraphEdge(f"user:{sp.host_id}", space_key, "OWNS"))
                edges.append(GraphEdge(user_key, host_key, "TRANSACTED_WITH", metadata={"booking_id": b.id}))

        # 3. Devices & IPs used by this user
        sessions = DeviceSession.query.filter_by(user_id=user_id).all()
        for s in sessions:
            if s.session_token_hash:
                dev_key = f"device:{s.session_token_hash}"
                cls._add_entity_node("DEVICE", s.session_token_hash, nodes)
                edges.append(GraphEdge(user_key, dev_key, "USED_DEVICE"))
            if s.ip_address:
                ip_key = f"ip:{s.ip_address}"
                cls._add_entity_node("IP", s.ip_address, nodes)
                edges.append(GraphEdge(user_key, ip_key, "USED_IP"))

        # Check telemetry events
        events = FraudEventRecord.query.filter_by(user_id=user_id).limit(20).all()
        for ev in events:
            if ev.device_fingerprint:
                dev_key = f"device:{ev.device_fingerprint}"
                cls._add_entity_node("DEVICE", ev.device_fingerprint, nodes)
                edges.append(GraphEdge(user_key, dev_key, "USED_DEVICE"))
            if ev.ip_address:
                ip_key = f"ip:{ev.ip_address}"
                cls._add_entity_node("IP", ev.ip_address, nodes)
                edges.append(GraphEdge(user_key, ip_key, "USED_IP"))

    @classmethod
    def _expand_space(cls, space_id: int, nodes: dict[str, GraphNode], edges: list[GraphEdge], depth: int) -> None:
        space = db.session.get(Space, space_id)
        if not space:
            return

        space_key = f"space:{space.id}"
        host_key = f"user:{space.host_id}"
        cls._add_entity_node("USER", str(space.host_id), nodes)
        edges.append(GraphEdge(host_key, space_key, "OWNS"))

        bookings = Booking.query.filter_by(space_id=space.id).limit(30).all()
        for b in bookings:
            b_key = f"booking:{b.id}"
            cls._add_entity_node("BOOKING", str(b.id), nodes)
            edges.append(GraphEdge(b_key, space_key, "RESERVES"))

            guest_key = f"user:{b.guest_id}"
            cls._add_entity_node("USER", str(b.guest_id), nodes)
            edges.append(GraphEdge(guest_key, b_key, "BOOKED"))
            edges.append(GraphEdge(guest_key, host_key, "TRANSACTED_WITH", metadata={"booking_id": b.id}))

    @classmethod
    def _expand_booking(cls, booking_id: int, nodes: dict[str, GraphNode], edges: list[GraphEdge], depth: int) -> None:
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return

        b_key = f"booking:{booking.id}"
        guest_key = f"user:{booking.guest_id}"
        space_key = f"space:{booking.space_id}"

        cls._add_entity_node("USER", str(booking.guest_id), nodes)
        cls._add_entity_node("SPACE", str(booking.space_id), nodes)
        edges.append(GraphEdge(guest_key, b_key, "BOOKED"))
        edges.append(GraphEdge(b_key, space_key, "RESERVES"))

        space = booking.space or db.session.get(Space, booking.space_id)
        if space:
            host_key = f"user:{space.host_id}"
            cls._add_entity_node("USER", str(space.host_id), nodes)
            edges.append(GraphEdge(host_key, space_key, "OWNS"))
            edges.append(GraphEdge(guest_key, host_key, "TRANSACTED_WITH", metadata={"booking_id": booking.id}))

    @classmethod
    def _expand_device(cls, device_fingerprint: str, nodes: dict[str, GraphNode], edges: list[GraphEdge], depth: int) -> None:
        dev_key = f"device:{device_fingerprint}"

        # Find users using this device
        sessions = DeviceSession.query.filter_by(session_token_hash=device_fingerprint).all()
        user_ids = {s.user_id for s in sessions}

        events = FraudEventRecord.query.filter_by(device_fingerprint=device_fingerprint).all()
        user_ids.update({e.user_id for e in events if e.user_id is not None})

        for uid in user_ids:
            u_key = f"user:{uid}"
            cls._add_entity_node("USER", str(uid), nodes)
            edges.append(GraphEdge(u_key, dev_key, "USED_DEVICE"))
            if depth > 1:
                cls._expand_user(uid, nodes, edges, depth - 1)

    @classmethod
    def _expand_ip(cls, ip_address: str, nodes: dict[str, GraphNode], edges: list[GraphEdge], depth: int) -> None:
        ip_key = f"ip:{ip_address}"

        sessions = DeviceSession.query.filter_by(ip_address=ip_address).all()
        user_ids = {s.user_id for s in sessions}

        events = FraudEventRecord.query.filter_by(ip_address=ip_address).all()
        user_ids.update({e.user_id for e in events if e.user_id is not None})

        for uid in user_ids:
            u_key = f"user:{uid}"
            cls._add_entity_node("USER", str(uid), nodes)
            edges.append(GraphEdge(u_key, ip_key, "USED_IP"))

    # -------------------------------------------------------------------------
    # Cycle and Cluster Analytics
    # -------------------------------------------------------------------------

    @classmethod
    def detect_user_cycles(cls, nodes: dict[str, GraphNode], max_cycle_length: int = 4) -> list[dict[str, Any]]:
        """Detect circular transaction cycles among users present in the graph or DB."""
        # Build directed transaction graph: A -> B means A booked B's space
        user_ids = [int(n.node_id.split(":")[1]) for n in nodes.values() if n.node_type == "USER"]
        if len(user_ids) < 2:
            return []

        adj: dict[int, set[int]] = defaultdict(set)

        # Query all bookings where guest is in user_ids
        bookings = Booking.query.filter(
            Booking.guest_id.in_(user_ids),
            Booking.status.in_(["confirmed", "active", "completed", "pending"]),
        ).all()

        for b in bookings:
            sp = b.space or db.session.get(Space, b.space_id)
            if sp and sp.host_id in user_ids and sp.host_id != b.guest_id:
                adj[b.guest_id].add(sp.host_id)

        detected_cycles: list[dict[str, Any]] = []
        visited_paths: set[tuple[int, ...]] = set()

        def dfs(current: int, path: list[int]):
            if len(path) > max_cycle_length:
                return

            for neighbor in adj.get(current, set()):
                if neighbor == path[0] and len(path) >= 2:
                    # Found cycle
                    canonical = cls._canonical_cycle(path)
                    if canonical not in visited_paths:
                        visited_paths.add(canonical)
                        detected_cycles.append({
                            "length": len(path),
                            "cycle_nodes": [f"user:{uid}" for uid in path] + [f"user:{path[0]}"],
                            "user_ids": path,
                            "cycle_type": "RECIPROCAL_PAIR" if len(path) == 2 else f"CIRCULAR_RING_{len(path)}",
                            "description": " -> ".join([f"User #{uid}" for uid in path] + [f"User #{path[0]}"]),
                        })
                elif neighbor not in path:
                    dfs(neighbor, path + [neighbor])

        for u in user_ids:
            dfs(u, [u])

        return detected_cycles

    @classmethod
    def _canonical_cycle(cls, path: list[int]) -> tuple[int, ...]:
        """Produce canonical rotation representation for cycle uniqueness."""
        n = len(path)
        rotations = [tuple(path[i:] + path[:i]) for i in range(n)]
        return min(rotations)

    @classmethod
    def detect_device_clusters(cls, nodes: dict[str, GraphNode]) -> list[dict[str, Any]]:
        """Identify device nodes connected to multiple distinct users."""
        device_nodes = [n for n in nodes.values() if n.node_type == "DEVICE"]
        clusters: list[dict[str, Any]] = []

        for dev in device_nodes:
            fingerprint = dev.metadata.get("fingerprint")
            if not fingerprint:
                continue

            sessions = DeviceSession.query.filter_by(session_token_hash=fingerprint).all()
            user_ids = {s.user_id for s in sessions}

            events = FraudEventRecord.query.filter_by(device_fingerprint=fingerprint).all()
            user_ids.update({e.user_id for e in events if e.user_id is not None})

            if len(user_ids) >= 2:
                clusters.append({
                    "device_node_id": dev.node_id,
                    "fingerprint": fingerprint,
                    "account_count": len(user_ids),
                    "user_ids": sorted(list(user_ids)),
                    "risk": "HIGH" if len(user_ids) == 2 else "CRITICAL",
                })

        return clusters
