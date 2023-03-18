#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="portfolio-balancer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ccxt",
        "toml",
        "argparse",
    ],
    author="Meir Michanie",
    author_email="meirm@riunx.com",
    description="A tool to balance a cryptocurrency portfolio",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/meirm/portfolio-balancer",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
