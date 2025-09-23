"""
Mirai Trading SDK - Setup Configuration
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mirai-trading-sdk",
    version="1.0.0",
    author="Mirai Trading Team",
    author_email="sdk@mirai-trading.com",
    description="Official Python SDK for Mirai Trading System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/mirai-agent",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/mirai-agent/issues",
        "Documentation": "https://docs.mirai-trading.com",
        "Source Code": "https://github.com/your-org/mirai-agent",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.19.0",
        ],
        "testing": [
            "pytest>=6.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.8.0",
            "aioresponses>=0.7.0",
        ],
    },
    include_package_data=True,
    package_data={
        "mirai_sdk": ["py.typed"],
    },
    keywords=[
        "trading", "cryptocurrency", "bitcoin", "ethereum", "binance",
        "algorithmic-trading", "quantitative-finance", "api-client",
        "sdk", "mirai", "autonomous-trading", "ai-trading"
    ],
    entry_points={
        "console_scripts": [
            "mirai-cli=mirai_sdk.cli:main",
        ],
    },
    zip_safe=False,
)