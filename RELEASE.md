# Release info
Steps for release are
* github: close and update issues/milestone
* update version number in develop branch
* fix pep8 issues (`tox -e pep8`)
* make sure all tests run (`tox -e py27`, `tox -e py35`)
* build documentation `docs_builder/make html`
* add changes to README changelog section
* github: merge all develop changes to master via pull request
* github: create release from master branch
* release on [pypi](https://pypi.python.org/pypi/sbmlutils)
```
python setup.py sdist upload
```
* test installation in virtualenv from pypi
```
(test) pip install sbmlutils
```
* switch to develop branch and increase version number
* update zenodo information (DOI & citation)