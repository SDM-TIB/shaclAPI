#!/usr/bin/env python3

from distutils.core import setup
from setuptools import find_packages

setup(name='travshaclAPI',
      version='1.0',
      description='travshaclAPI',
      packages=find_packages(),
      install_requires=['SPARQLWrapper','flask','rdflib','requests','pyinstrument','PyYaml'],
      include_package_data=True,
      python_requires='>=3.8',
      zip_safe=False)
