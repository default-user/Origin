#!/usr/bin/env python3
# RealityWeaverVideo Setup
# Attribution: Ande → Kai
# License: WCL-1.0

from setuptools import setup, find_packages

setup(
    name="realityweaver-video",
    version="1.0.0",
    description="Video processing pipeline with auditable packaging",
    author="Ande Turner & Contributors",
    license="WCL-1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    extras_require={
        "ffmpeg": ["ffmpeg-python"],
        "metrics": ["vmaf"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
