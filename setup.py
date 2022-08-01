#!/usr/bin/env python3

from distutils.core import setup
from setuptools import find_packages

setup(name='shaclapi',
      version='1.0.0',
      description='shaclapi',
      packages=find_packages(exclude='tests'),
      install_requires=[
            'SPARQLWrapper==2.0.0',
            'requests==2.27.1',
            'SHACL2SPARQLpy==1.1.0',
            'TravSHACL==1.0.0',
            'multiprocessing_logging==0.3.1',
            'regex==2022.3.15'
      ],
      include_package_data=False,
      python_requires='>=3.8',
      zip_safe=False)
