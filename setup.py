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

setup_kwargs = {}

# version string
try:
    import re
    VERSIONFILE = "sbmlutils/_version.py"
    verstrline = codecs.open(VERSIONFILE, "rt").read()
    mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", verstrline, re.M)
    if mo:
        verstr = mo.group(1)
        setup_kwargs['version'] = verstr
    else:
        raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))
except Exception as e:
    print('Could not read version: {}'.format(e))

# description
try:
    with open('README.md') as handle:
        readme = handle.read()
    setup_kwargs["long_description"] = readme
except:
    setup_kwargs["long_description"] = ''

setup(
    name='sbmlutils',
    version=verstr,
    description='SBML python utilities',
    long_description='SBML python utilities',
    url='https://github.com/matthiaskoenig/sbmlutils',
    author='Matthias Koenig',
    author_email='konigmatt@googlemail.com',
    license='LGPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v3'
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
    packages=find_packages(),  # ['sbmlutils'],
    package_data={'': ['test/data/*']},

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "python-libsbml",
        "libroadrunner",
        "cobra",
        "pandas",
        "tabulate",
        "Jinja2",
        "pyexcel",
        "pyexcel-xlsx",
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
    
    # include the package distribution_data
    include_package_data=True,

    # Prevent the package manager to install a python egg, 
    # instead you'll get a real directory with files in it.
    zip_safe=False,

)
