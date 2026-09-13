from setuptools import find_packages, setup

setup(
    name="thegent-dspy",
    version="0.1.0",
    description="DSPy-style compiler and teleprompter for thegent",
    author="Phenotype",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "dev": ["pytest", "ruff"],
    },
)
