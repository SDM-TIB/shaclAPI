#!/usr/bin/env python3
from distutils.core import setup
from setuptools import find_packages

VERSION = '0.9.6'

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='shaclapi',
    version=VERSION,
    description='An API implementing optimizations over SHACL validators.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GNU/GPLv3',
    author='Julian Gercke, Philipp D. Rohde, Fabian Johannsen',
    author_email='philipp.rohde@tib.eu',
    url='https://github.com/SDM-TIB/shaclAPI',
    download_url='https://github.com/SDM-TIB/shaclAPI/archive/refs/tags/v' + VERSION + '.tar.gz',
    packages=find_packages(exclude='tests'),
    install_requires=[
        'SPARQLWrapper>=2.0.0',
        'requests>=2.27.1',
        'SHACL2SPARQLpy>=1.1.1',
        'TravSHACL>=1.0.2',
        'multiprocessing_logging>=0.3.1',
        'regex>=2022.3.15'
    ],
    include_package_data=True,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research'
    ]
)
