#!/usr/bin/env python3
# RealityWeaver Setup
# Attribution: Ande → Kai
# License: WCL-1.0

from setuptools import setup, find_packages

setup(
    name="realityweaver",
    version="1.0.0",
    description="Block-based compression with adaptive codec racing",
    author="Ande Turner & Contributors",
    license="WCL-1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "realityweaver=cli:main",
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
