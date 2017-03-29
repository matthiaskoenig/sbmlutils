#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
see
    https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure

source distribution generation via
python setup.py sdist
"""

from __future__ import absolute_import, print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    """ Read file info in correct encoding. """
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup_kwargs = {}
try:
    verstrline = read('sbmlutils/_version.py')
    mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", verstrline, re.M)
    if mo:
        verstr = mo.group(1)
        setup_kwargs['version'] = verstr
    else:
        raise RuntimeError("Unable to find version string")
except Exception as e:
    print('Could not read version: {}'.format(e))


setup(
    name='sbmlutils',
    description='SBML python utilities',
    long_description='SBML python utilities',
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
      '': ['tests/data'],
    },
    # py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "python-libsbml>=5.13.0",
        "libroadrunner>=1.4.15",
        "cobra>=0.6.0a4",
        # "antimony>2.9.0",
        "pandas",
        "tabulate",
        "Jinja2",
        "pyexcel",
        "pyexcel-xlsx",
        "six",
    ],
    extras_require={},
    **setup_kwargs)
