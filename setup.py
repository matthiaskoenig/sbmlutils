#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
sbmlutils pip package
"""
from __future__ import absolute_import, print_function

import io
import re
import os
from setuptools import find_packages
from setuptools import setup

setup_kwargs = {}


def read(*names, **kwargs):
    """ Read file info in correct encoding. """
    return io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


# version from file
verstrline = read('sbmlutils/_version.py')
mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", verstrline, re.M)
if mo:
    verstr = mo.group(1)
    setup_kwargs['version'] = verstr
else:
    raise RuntimeError("Unable to find version string")

# description from markdown
long_description = read('README.rst')
setup_kwargs['long_description'] = long_description

setup(
    name='sbmlutils',
    description='SBML python utilities',
    url='https://github.com/matthiaskoenig/sbmlutils',
    author='Matthias König',
    author_email='konigmatt@googlemail.com',
    license='LGPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Cython',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    keywords='SBML, dynamic FBA, DFBA, model merging',
    packages=find_packages(),
    # package_dir={'': ''},
    package_data={
      '': ['../requirements.txt',
           'tests/data'],
    },
    include_package_data=True,
    zip_safe=False,
    # List run-time dependencies here.  These will be installed by pip when
    install_requires=[
        "pip>=18.0",
        "numpy>=1.14.5",
        "scipy>=1.1.0",
        "matplotlib>=2.2.2",
        "pandas>=0.23.1",
        "tabulate>=0.8.2",
        "Jinja2>=2.10",
        "requests>=2.19.0",
        "beautifulsoup4>=4.6.0",
        "xarray>=0.10.7",
        "pyexcel>=0.5.8",
        "pyexcel-xlsx>=0.5.6",
        # fba
        "cobra>=0.13.0",
        "optlang>=1.4.2",
        # standards
        "libroadrunner>=1.4.24",
        "tesbml>=5.15.0.1",
        "tesedml>=0.4.3",
        "tecombine>=0.2.2.1",
        "tenuml>=1.1.1",
        "phrasedml>=1.0.9",
        "antimony>=2.9.4",
        "tellurium>=2.0.18",
        # testing
        "pytest>=3.6.1",
        "pytest-cov>=2.5.1",
        # misc
        "ipykernel>=4.8.2",
    ],
    extras_require={},
    **setup_kwargs)
