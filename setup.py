"""
Setup configuration for meshtrbl package.
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
    name="meshtrbl",
    version="3.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered troubleshooting agent for Kubernetes and Consul service mesh",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chrislovett/meshtrbl",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "workflow": [
            "langgraph>=0.1.0,<0.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "meshtrbl=src.agent:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["prompts/*.py"],
        "": ["*.yaml", "*.yml", "*.md"],
    },
    zip_safe=False,
)

# Made with Bob
