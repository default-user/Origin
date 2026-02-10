"""Tests for RW-4 (capture) and RW-7 (stream): gated, default off."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.capture import (
    CaptureDisabledError,
    CapturePolicy,
    ConsentRequiredError,
    start_capture,
    stop_capture,
    validate_capture_policy,
)
from origin.utilities.realityweaver.stream import (
    StreamDisabledError,
    StreamPolicy,
    start_stream,
    stop_stream,
    validate_stream_policy,
)


class TestCaptureDefaultOff:
    """C3-T1, C3-T2, C3-T3: Capture default off tests."""

    def test_c3_t1_default_capture_disabled(self):
        """C3-T1: Fresh policy has capture=false."""
        policy = CapturePolicy()
        assert not policy.enabled
        errors = validate_capture_policy(policy)
        assert any("disabled" in e for e in errors)

    def test_c3_t3_capture_without_governance_fails(self):
        """C3-T3: Enabling capture without governance token fails."""
        policy = CapturePolicy(enabled=True, consent_given=True)
        errors = validate_capture_policy(policy)
        assert any("governance" in e for e in errors)

    def test_capture_without_consent_fails(self):
        """C2-T1: Capture without consent emits fail."""
        policy = CapturePolicy(enabled=True, consent_given=False, governance_token="tok")
        try:
            start_capture(policy)
            assert False, "Should have raised"
        except ConsentRequiredError:
            pass

    def test_capture_disabled_raises(self):
        policy = CapturePolicy(enabled=False)
        try:
            start_capture(policy)
            assert False, "Should have raised"
        except CaptureDisabledError:
            pass

    def test_valid_capture_starts(self):
        policy = CapturePolicy(
            enabled=True,
            consent_given=True,
            governance_token="valid-token",
        )
        session = start_capture(policy)
        assert session.active
        assert session.session_id.startswith("RWCS-")

    def test_stop_capture_emits_receipt(self):
        policy = CapturePolicy(
            enabled=True,
            consent_given=True,
            governance_token="valid-token",
        )
        session = start_capture(policy)
        receipt = stop_capture(session)
        assert receipt["operation"] == "capture_stop"
        assert receipt["passed"]
        assert not session.active


class TestStreamDefaultOff:
    """C3-T2 + stream gating tests."""

    def test_c3_t2_default_stream_disabled(self):
        """C3-T2: Fresh policy has stream=false."""
        policy = StreamPolicy()
        assert not policy.enabled
        errors = validate_stream_policy(policy)
        assert any("disabled" in e for e in errors)

    def test_stream_without_governance_fails(self):
        policy = StreamPolicy(enabled=True, scope="local")
        try:
            start_stream(policy)
            assert False, "Should have raised"
        except StreamDisabledError:
            pass

    def test_stream_with_no_scope_fails(self):
        policy = StreamPolicy(enabled=True, scope="none", governance_token="tok")
        try:
            start_stream(policy)
            assert False, "Should have raised"
        except StreamDisabledError:
            pass

    def test_valid_stream_starts(self):
        policy = StreamPolicy(
            enabled=True,
            scope="local",
            governance_token="valid-token",
        )
        session = start_stream(policy)
        assert session.active
        assert session.session_id.startswith("RWSS-")

    def test_stop_stream_emits_receipt(self):
        policy = StreamPolicy(
            enabled=True,
            scope="local",
            governance_token="valid-token",
        )
        session = start_stream(policy)
        receipt = stop_stream(session)
        assert receipt["operation"] == "stream_stop"
        assert receipt["passed"]
        assert not session.active
