# Origin Weaver Integration Module
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Unified interface for all Weaver modules in Origin.

This module provides Origin-native integration points for:
- compress_bytes / decompress_bytes (RWV1)
- phraseweave_encode / phraseweave_decode
- pwk_check (ProofWeave kernel)
- rwv_video_run_pipeline (video processing)

All functions follow Origin's determinism and fail-closed principles.
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple

# Add module paths
_module_base = os.path.dirname(os.path.abspath(__file__))
for module_name in ['realityweaver', 'phraseweave', 'proofweave', 'realityweaver_video',
                     'realityweaver_music']:
    module_path = os.path.join(_module_base, module_name, 'src')
    if module_path not in sys.path:
        sys.path.insert(0, module_path)


# =============================================================================
# RealityWeaver (RWV1) Integration
# =============================================================================

def compress_bytes(data: bytes, config: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Compress bytes using RealityWeaver (RWV1).

    Args:
        data: Raw bytes to compress
        config: Optional configuration dict with keys:
            - block_size: Block size in bytes (default: 1MB)
            - allow_bz2: Enable bz2 branch (default: False)
            - allow_lzma: Enable lzma branch (default: False)
            - include_sha256: Store integrity hash (default: False)

    Returns:
        RWV1 container bytes

    Invariant: decompress_bytes(compress_bytes(x)) == x
    """
    from container import compress_bytes as _compress, RWV1Config

    if config:
        cfg = RWV1Config(
            block_size=config.get('block_size', 1 << 20),
            allow_bz2=config.get('allow_bz2', False),
            allow_lzma=config.get('allow_lzma', False),
            include_sha256=config.get('include_sha256', False),
        )
    else:
        cfg = None

    return _compress(data, cfg)


def decompress_bytes(container: bytes) -> bytes:
    """
    Decompress RWV1 container to original bytes.

    Args:
        container: RWV1 container bytes

    Returns:
        Original raw bytes

    Raises:
        Exception on decompression failure or integrity check failure
    """
    from container import decompress_bytes as _decompress
    return _decompress(container)


# =============================================================================
# PhraseWeave (PWV1) Integration
# =============================================================================

def phraseweave_encode(
    raw: bytes,
    dictionary: Optional[Dict[int, bytes]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Encode bytes using PhraseWeave (PWV1).

    Args:
        raw: Raw bytes to encode
        dictionary: Optional dict mapping stan_id -> raw_form bytes
        config: Optional configuration dict with keys:
            - min_phrase_len: Minimum phrase length (default: 2)
            - max_phrase_len: Maximum phrase length (default: 64)
            - greedy: Use greedy matching (default: True)

    Returns:
        Tuple of (woven bytes, metadata dict)

    Invariant: phraseweave_decode(phraseweave_encode(x)[0]) == x
    """
    from codec import phraseweave_encode as _encode
    from dictionary import Dictionary
    from types import Config

    # Build dictionary
    dict_obj = Dictionary()
    if dictionary:
        for stan_id, raw_form in dictionary.items():
            dict_obj.add_entry(stan_id, raw_form)

    # Build config
    cfg = Config(
        min_phrase_len=config.get('min_phrase_len', 2) if config else 2,
        max_phrase_len=config.get('max_phrase_len', 64) if config else 64,
        greedy=config.get('greedy', True) if config else True,
    )

    woven, metadata = _encode(raw, dict_obj, cfg)
    return woven, metadata.to_dict()


def phraseweave_decode(
    woven: bytes,
    dictionary: Optional[Dict[int, bytes]] = None,
    config: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Decode PhraseWeave (PWV1) woven bytes.

    Args:
        woven: PWV1 woven bytes
        dictionary: Dict mapping stan_id -> raw_form bytes (must match encoded)
        config: Optional configuration dict with keys:
            - max_output_size: Maximum output size (fail-closed)

    Returns:
        Original raw bytes

    Raises:
        Exception on decoding failure or dictionary mismatch
    """
    from codec import phraseweave_decode as _decode
    from dictionary import Dictionary
    from types import Config

    # Build dictionary
    dict_obj = Dictionary()
    if dictionary:
        for stan_id, raw_form in dictionary.items():
            dict_obj.add_entry(stan_id, raw_form)

    # Build config
    cfg = Config(
        max_output_size=config.get('max_output_size') if config else None,
    )

    return _decode(woven, dict_obj, cfg)


# =============================================================================
# ProofWeave (PWK) Integration
# =============================================================================

def pwk_check(pwof: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check a PWOF proof object using the trusted PWK kernel.

    Args:
        pwof: PWOF v1 proof object (dict)

    Returns:
        Result dict with keys:
            - passed: bool
            - message: str
            - node_count: int (if passed)
            - rules_used: list (if passed)

    The kernel is TRUSTED. Everything else (engines, tactics, LLMs) is UNTRUSTED.
    """
    from kernel import pwk_check as _check

    result = _check(pwof)
    return {
        'passed': result.passed,
        'message': result.message,
        'node_count': result.node_count,
        'rules_used': result.rules_used,
    }


def pwof_hash(pwof: Dict[str, Any], algorithm: str = 'sha256') -> str:
    """
    Compute canonical hash of a PWOF proof object.

    Args:
        pwof: PWOF proof object (dict)
        algorithm: Hash algorithm ('sha256' or 'blake3')

    Returns:
        Hex-encoded hash string
    """
    from canonicalize import compute_hash
    return compute_hash(pwof, algorithm)


# =============================================================================
# RealityWeaverVideo Integration
# =============================================================================

def rwv_video_run_pipeline(
    input_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run video processing pipeline.

    Args:
        input_path: Path to input video
        output_path: Path for output video
        config: Optional configuration dict with keys:
            - segment_duration: Segment duration in seconds (default: 4.0)
            - vmaf_threshold: VMAF quality threshold (default: 95.0)
            - enabled_encoders: List of encoder configs

    Returns:
        Result dict with keys:
            - success: bool
            - error: str or None
            - segments: list of segment results
            - compression_ratio: float
            - manifest_path: str (if manifest saved)

    Note: This is a skeleton implementation. Full functionality requires
    ffmpeg and metric computation tools.
    """
    from pipeline import VideoPipeline, PipelineConfig

    if config:
        cfg = PipelineConfig(
            segment_duration=config.get('segment_duration', 4.0),
            vmaf_threshold=config.get('vmaf_threshold', 95.0),
        )
    else:
        cfg = None

    pipeline = VideoPipeline(cfg)
    result = pipeline.run(input_path, output_path)

    return result.to_dict()


# =============================================================================
# RealityWeaverMusic (RXM1) Integration
# =============================================================================

def rxm_pack_bytes(
    metadata: Dict[str, Any],
    score_data: bytes,
    audio_data: Optional[bytes] = None,
    sync_entries: Optional[list] = None,
    config: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Pack data into an RXM1 (Reality Weaver Music) container.

    Args:
        metadata: Metadata dict with keys: title, composer, tempo_bpm,
            time_signature, key_signature, score_format, audio_format
        score_data: Raw score data (MIDI bytes)
        audio_data: Optional raw audio data
        sync_entries: Optional list of [score_tick, audio_frame] pairs
        config: Optional configuration dict with keys:
            - include_sha256: Store integrity hash (default: False)
            - rwv1_block_size: Block size for compression (default: 1MB)

    Returns:
        RXM1 container bytes

    Invariant: rxm_unpack_bytes(rxm_pack_bytes(meta, score, audio, sync))
               reproduces all inputs.
    """
    from container import pack_bytes as _pack
    from rxm_types import RXMMetadata, RXMConfig, SyncEntry

    meta = RXMMetadata.from_dict(metadata) if metadata else RXMMetadata()

    cfg = None
    if config:
        cfg = RXMConfig(
            include_sha256=config.get('include_sha256', False),
            rwv1_block_size=config.get('rwv1_block_size', 1 << 20),
            rwv1_allow_bz2=config.get('rwv1_allow_bz2', False),
            rwv1_allow_lzma=config.get('rwv1_allow_lzma', False),
        )

    sync = None
    if sync_entries:
        sync = [SyncEntry(score_tick=e[0], audio_frame=e[1])
                for e in sync_entries]

    return _pack(meta, score_data, audio_data, sync, cfg)


def rxm_unpack_bytes(container: bytes) -> Dict[str, Any]:
    """
    Unpack an RXM1 container.

    Args:
        container: RXM1 container bytes

    Returns:
        Dict with keys:
            - metadata: dict
            - score_data: bytes
            - audio_data: bytes or None
            - sync_entries: list of [tick, frame] pairs or None
    """
    from container import unpack_bytes as _unpack

    result = _unpack(container)
    return {
        'metadata': result['metadata'].to_dict(),
        'score_data': result['score_data'],
        'audio_data': result['audio_data'],
        'sync_entries': (
            [[e.score_tick, e.audio_frame] for e in result['sync_entries']]
            if result['sync_entries'] else None
        ),
    }


# =============================================================================
# Module Registration
# =============================================================================

WEAVER_MODULES = {
    'realityweaver': {
        'version': '1.0.0',
        'functions': ['compress_bytes', 'decompress_bytes'],
        'formats': ['RWV1'],
    },
    'phraseweave': {
        'version': '1.0.0',
        'functions': ['phraseweave_encode', 'phraseweave_decode'],
        'formats': ['PWV1', 'PWDC'],
    },
    'proofweave': {
        'version': '1.0.0',
        'functions': ['pwk_check', 'pwof_hash'],
        'formats': ['PWOF_v1'],
        'rulesets': ['PWK_ND_PROP_EQ_v1'],
    },
    'realityweaver_video': {
        'version': '1.0.0',
        'functions': ['rwv_video_run_pipeline'],
        'formats': ['RWV-VIDEO-V1'],
        'status': 'skeleton',
    },
    'realityweaver_music': {
        'version': '1.0.0',
        'functions': ['rxm_pack_bytes', 'rxm_unpack_bytes'],
        'formats': ['RXM1'],
        'reuses': ['RWV1'],
    },
}


def get_module_info() -> Dict[str, Any]:
    """Get information about registered Weaver modules."""
    return {
        'weaver_version': '1.0.0',
        'modules': WEAVER_MODULES,
        'license': 'WCL-1.0',
        'attribution': 'Ande → Kai',
    }
