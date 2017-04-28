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
from os.path import dirname
from os.path import join

from setuptools import find_packages
from setuptools import setup

import pip

# parse requirements.txt (packages and github links)
links = []
requires = []

try:
    requirements = pip.req.parse_requirements('requirements.txt')
except:
    # new versions of pip requires a session
    requirements = pip.req.parse_requirements(
        'requirements.txt', session=pip.download.PipSession())

for item in pip.req.parse_requirements(
        'requirements.txt', session=pip.download.PipSession()):
    # we want to handle package names and also repo urls
    if getattr(item, 'url', None):  # older pip has url
        links.append(str(item.url))
    if getattr(item, 'link', None):  # newer pip has link
        links.append(str(item.link))
    if item.req:
        requires.append(str(item.req))


# read the version and info file
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

# descripion from markdown
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()
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
    install_requires=requires,
    dependency_links=links,
    extras_require={},
    **setup_kwargs)
