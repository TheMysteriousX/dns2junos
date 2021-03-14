import os

from setuptools import setup, find_packages

long_desc = open("README.md").read()

if os.path.exists("README.rst"):
    long_desc = open("README.rst").read()

setup(
    name="dns2junos",
    version="0.0.1",
    packages=find_packages(),
    entry_points={"console_scripts": ["dns2junos=scripts.dns2junos:main"]},
    license="Apache Software License",
    long_description=long_desc,
    author="Adam Bishop",
    author_email="adam@omega.org.uk",
    description="Accepts a DNS address, and resolves it to an address book entry for JunOS",
    url="https://github.com/TheMysteriousX/dns2junos",
    classifiers=["Development Status :: 4 - Beta", "License :: OSI Approved :: Apache Software License", "Programming Language :: Python :: 3.6"],
    python_requires='>=3.6',
    install_requires=['dnspython'],
)
