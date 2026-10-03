from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aset",
    version="1.0.0",
    author="ASET Team",
    author_email="team@aset.local",
    description="Advanced Stock Analysis Engine Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/artclass11/ASET",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aset=app.cli:cli",
        ],
    },
)
