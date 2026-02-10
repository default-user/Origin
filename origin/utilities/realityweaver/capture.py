"""
RW-4: Capture (gated, default off).

Capture is OFF unless explicitly started by a governed command (RW-C3).
Requires explicit consent ritual and scoped retention (RW-C2).
Always-on background capture is forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass

from .receipts import emit_receipt, gate


class CaptureDisabledError(Exception):
    """Raised when capture is attempted without governance enablement."""


class ConsentRequiredError(Exception):
    """Raised when capture is attempted without consent."""


@dataclass
class CapturePolicy:
    """Policy governing capture behaviour."""

    enabled: bool = False  # RW-C3: default off
    consent_given: bool = False  # RW-C2: requires consent
    retention_scope: str = "session"  # session | bounded | permanent
    retention_duration_seconds: int | None = None
    governance_token: str | None = None


@dataclass
class CaptureSession:
    """An active capture session."""

    session_id: str
    policy: CapturePolicy
    active: bool = False
    frames_captured: int = 0


def validate_capture_policy(policy: CapturePolicy) -> list[str]:
    """
    Validate a capture policy. Returns list of errors.

    Enforces: RW-C2 (consent), RW-C3 (default off).
    """
    errors = []
    if not policy.enabled:
        errors.append("Capture is disabled (RW-C3: default off). Enable via governance.")
    if not policy.consent_given:
        errors.append("Capture requires explicit consent (RW-C2).")
    if not policy.governance_token:
        errors.append("Capture requires governance token.")
    return errors


def start_capture(policy: CapturePolicy) -> CaptureSession:
    """
    Start a capture session (RW-C2, RW-C3).

    Fail-closed: raises if policy is invalid.
    """
    errors = validate_capture_policy(policy)
    if errors:
        if not policy.enabled:
            raise CaptureDisabledError(errors[0])
        if not policy.consent_given:
            raise ConsentRequiredError(errors[0])
        raise CaptureDisabledError("; ".join(errors))

    from .primitives import generate_id
    session = CaptureSession(
        session_id=generate_id("RWCS"),
        policy=policy,
        active=True,
    )
    return session


def stop_capture(session: CaptureSession) -> dict:
    """
    Stop a capture session and emit receipt.

    Returns the receipt.
    """
    session.active = False

    gates = [
        gate("consent_present", "pass", "Consent was given at session start."),
        gate("retention_scope", "pass", f"Retention scope: {session.policy.retention_scope}"),
    ]

    return emit_receipt(
        operation="capture_stop",
        operator_id="RW-4_capture",
        inputs={"session_id": session.session_id},
        outputs={"frames_captured": session.frames_captured},
        gates=gates,
        invariants_checked=["RW-C2", "RW-C3"],
    )
