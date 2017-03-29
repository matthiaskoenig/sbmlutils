# Release info
Steps for release are
* update version number in develop branch
* fix pep8 issues (`tox -e pep8`)
* make sure all tests run (`tox -e py27`, `tox -e py35`)
* build documentation `docs_builder/make html`
* add changes to README changelog section
* merge all develop changes to master via pull request
* create release from master branch in github
* release on [pypi](https://pypi.python.org/pypi/sbmlutils)
```
python setup.py sdist upload
```
* switch to develop branch and increase version number
* update zenodo information (DOI & citation)