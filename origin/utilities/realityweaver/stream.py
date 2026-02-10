"""
RW-7: Stream (gated, default off).

Streaming is OFF by default. Requires governance enablement.
Always-on background streaming is forbidden. Scope-bounded.
"""

from __future__ import annotations

from dataclasses import dataclass

from .receipts import emit_receipt, gate


class StreamDisabledError(Exception):
    """Raised when streaming is attempted without governance enablement."""


@dataclass
class StreamPolicy:
    """Policy governing stream behaviour."""

    enabled: bool = False  # default off
    scope: str = "none"  # none | local | scoped_external
    governance_token: str | None = None


@dataclass
class StreamSession:
    """An active stream session."""

    session_id: str
    policy: StreamPolicy
    active: bool = False
    bytes_streamed: int = 0


def validate_stream_policy(policy: StreamPolicy) -> list[str]:
    """
    Validate a stream policy. Returns list of errors.
    """
    errors = []
    if not policy.enabled:
        errors.append("Stream is disabled (default off). Enable via governance.")
    if policy.scope == "none":
        errors.append("Stream scope is 'none'. Set a valid scope.")
    if not policy.governance_token:
        errors.append("Stream requires governance token.")
    return errors


def start_stream(policy: StreamPolicy) -> StreamSession:
    """
    Start a stream session.

    Fail-closed: raises if policy is invalid.
    """
    errors = validate_stream_policy(policy)
    if errors:
        raise StreamDisabledError("; ".join(errors))

    from .primitives import generate_id
    session = StreamSession(
        session_id=generate_id("RWSS"),
        policy=policy,
        active=True,
    )
    return session


def stop_stream(session: StreamSession) -> dict:
    """
    Stop a stream session and emit receipt.

    Returns the receipt.
    """
    session.active = False

    gates = [
        gate("scope_bounded", "pass", f"Scope: {session.policy.scope}"),
        gate("governance_token", "pass", "Governance token was present."),
    ]

    return emit_receipt(
        operation="stream_stop",
        operator_id="RW-7_stream",
        inputs={"session_id": session.session_id},
        outputs={"bytes_streamed": session.bytes_streamed},
        gates=gates,
        invariants_checked=["RW-C3"],
    )
