#!/usr/bin/env python
from setuptools import setup, find_packages

with open('README.md', 'r') as readme:
    long_description = readme.read()

setup(
    name='pampinus',
    version='0.1',
    packages=find_packages(),
    scripts=['pampinus/manage.py'],
    description='Dashboard for WMF Database Backups',
    long_description=long_description,
    url="https://phabricator.wikimedia.org/diffusion/OSPM/",
    install_requires=[
        'Django==3.2',
        'mysqlclient',
        'wmfbackups @ git+https://gerrit.wikimedia.org/r/operations/software/wmfbackups'],
)
