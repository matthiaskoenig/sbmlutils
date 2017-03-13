"""Setup module for odesim.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject

source distribution generation via
python setup.py sdist
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import codecs  # To use a consistent encoding
import os

here = os.path.abspath(os.path.dirname(__file__))

# get the version
import re
VERSIONFILE = "sbmlutils/_version.py"
verstrline = codecs.open(VERSIONFILE, "rt").read()
mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(
    name='sbmlutils',
    version=verstr,
    description='SBML python utilities',
    long_description='SBML python utilities',
    url='https://github.com/matthiaskoenig/sbmlutils',

    # Author details
    author='Matthias Koenig',
    author_email='konigmatt@googlemail.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords='SBML',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # exclude=['contrib', 'docs', 'examples*']
    packages=['sbmlutils'],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        # "python-libsbml",
        # "libroadrunner",
        # "Cython",
        # "pandas",
        # "tabulate",
        # "cobra",
        # "Jinja2",
        # "pyexcel",
        # "pyexcel-xlsx",
        # "nose",
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    # extras_require={
    #     'dev': ['check-manifest'],
    #    'test': ['coverage'],
    # },

    # If there are distribution_data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    #    'sample': ['package_data.dat'],
    # },
    
    # include the package distribution_data (SBGN, XSD)
    include_package_data=True,

    # Prevent the package manager to install a python egg, 
    # instead you'll get a real directory with files in it.
    zip_safe=False,

)
