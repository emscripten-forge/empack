#!/usr/bin/env python

"""The setup script."""
from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = ["typer", "requests", "pydantic", "pyyaml", "pydantic", "appdirs", "networkx"]

setup(
    author="Thorsten Beier",
    author_email="derthorstenbeier@gmail.com",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    data_files=[("share/empack", ["config/empack_config.yaml"])],
    description="empack emscripten+boa",
    entry_points={
        "console_scripts": [
            "empack=empack.cli.main:app",
        ],
    },
    install_requires=requirements,
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="empack",
    name="empack",
    packages=find_packages(),
    url="https://github.com/emscripten-forge/empack",
    version="2.0.9",
    zip_safe=False,
)
