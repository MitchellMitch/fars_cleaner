#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="fars_cleaner",
    version="1.4.0",
    description="A package for loading and preprocessing the NHTSA FARS crash database",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Mitchell Abrams",
    author_email="mitchell.abrams@duke.edu",
    maintainer="Mitchell Abrams",
    maintainer_email="mitchell.abrams@duke.edu",
    url="https://github.com/mzabrams/fars-cleaner",
    license="BSD-3-Clause",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.22.0",
        "scipy>=1.7.0",
        "pathlib",
        "pyjanitor>=0.23.1",
        "dask==2025.05.0",
        "distributed>=2022",
        "urllib3>=2.0.0",
        "tqdm>=4.64.0",
        "thefuzz",
        "pyarrow",
    ],
    extras_require={
        "dev": ["pytest>=7.1.0", "hypothesis"],
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent", 
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 5 - Production/Stable",
    ],
    keywords=[
        "FARS",
        "crash analysis",
        "data preprocessing",
        "NHTSA",
        "vehicle safety"
    ],
    include_package_data=True,
) 