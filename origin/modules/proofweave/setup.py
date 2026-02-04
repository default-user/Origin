#!/usr/bin/env python3
# ProofWeave Setup
# Attribution: Ande → Kai
# License: WCL-1.0

from setuptools import setup, find_packages

setup(
    name="proofweave",
    version="1.0.0",
    description="Deterministic proof format with trusted kernel checker",
    author="Ande Turner & Contributors",
    license="WCL-1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "pwk=cli:main",
        ],
    },
    extras_require={
        "blake3": ["blake3"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
