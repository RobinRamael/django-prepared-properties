#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = ["django>=2"]

setup_requirements = []

test_requirements = []

setup(
    author="Robin Ramael",
    author_email="robin.ramael@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Declarative annotations and prefetches for Django models",
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="prepared_properties",
    name="prepared_properties",
    packages=find_packages(
        include=["prepared_properties", "prepared_properties.*"]
    ),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/robinramael/django-prepared-properties",
    version="1.0.3",
    zip_safe=False,
)
