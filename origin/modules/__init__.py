# Origin Weaver Modules
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Origin Weaver Modules Integration.

This package provides integration points for the Weaver framework modules:
- RealityWeaver: Block-based compression with codec racing
- PhraseWeave: Reversible dictionary-based encoding
- ProofWeave: Deterministic proof format with trusted kernel
- RealityWeaverVideo: Video pipeline with quality gates

Usage:
    from origin.modules import weaver

    # Compression
    compressed = weaver.compress_bytes(data)
    original = weaver.decompress_bytes(compressed)

    # PhraseWeave
    woven, meta = weaver.phraseweave_encode(data, dictionary)
    raw = weaver.phraseweave_decode(woven, dictionary)

    # ProofWeave
    result = weaver.pwk_check(proof_object)

    # Video (skeleton)
    result = weaver.rwv_video_run_pipeline(input_path, config)
"""

__version__ = '1.0.0'
__author__ = 'Ande Turner & Contributors'
__license__ = 'WCL-1.0'
