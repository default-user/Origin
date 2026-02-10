#!/usr/bin/env python3
# RealityWeaverMusic Setup
# Attribution: Ande → Kai
# License: WCL-1.0

from setuptools import setup, find_packages

setup(
    name="realityweaver-music",
    version="1.0.0",
    description="Chunk-based music container with score and synced audio",
    author="Ande Turner & Contributors",
    license="WCL-1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "realityweaver>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "rxm=cli:main",
        ],
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
