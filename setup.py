"""Setup configuration for Stray SDK."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stray-sdk",
    version="0.1.0",
    author="sceptejas",
    description="A CLI tool for Stellar blockchain payments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sceptejas/Stray-SDK",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "stellar-sdk>=9.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "stellar-agent=stellar_agent.cli:run",
        ],
    },
)
