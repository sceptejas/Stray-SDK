"""Setup configuration for Stray-SDK."""
from setuptools import setup, find_packages

with open("Readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stray-sdk",
    version="1.1.0",
    author="Stray-SDK Contributors",
    author_email="",
    description="A lightweight Python CLI tool for sending XLM payments on the Stellar blockchain network",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/omolobamoyinoluwa-max/Stray-SDK",
    project_urls={
        "Bug Tracker": "https://github.com/omolobamoyinoluwa-max/Stray-SDK/issues",
        "Source Code": "https://github.com/omolobamoyinoluwa-max/Stray-SDK",
        "Documentation": "https://github.com/omolobamoyinoluwa-max/Stray-SDK/blob/main/Readme.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
        "Topic :: Internet",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    keywords="stellar blockchain cryptocurrency xlm payments cli",
    python_requires=">=3.8",
    install_requires=[
        "stellar-sdk==13.2.1",
        "python-dotenv==1.2.1",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest==9.0.2",
            "pytest-cov==6.0.0",
            "pytest-mock==3.14.0",
            "setuptools==75.0.0",
        ],
        "test": [
            "pytest==9.0.2",
            "pytest-cov==6.0.0",
            "pytest-mock==3.14.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stray-sdk=stellar_agent.cli:run",
            "stellar-agent=stellar_agent.cli:run",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
