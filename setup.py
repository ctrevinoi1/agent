from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="camel-osint",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="CAMEL-based multi-agent system for OSINT analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/camel-osint",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.101.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.3.0",
        "python-multipart>=0.0.6",
        "python-dotenv>=1.0.0",
        "openai>=1.3.0",
        "camel-ai>=0.1.0",
        "pyside6>=6.5.0",
        "websockets>=11.0.0",
        "requests>=2.31.0",
        "aiohttp>=3.8.0",
        "sqlalchemy>=2.0.0",
        "sqlitedict>=2.1.0",
    ],
    entry_points={
        "console_scripts": [
            "camel-osint=main:main",
        ],
    },
) 