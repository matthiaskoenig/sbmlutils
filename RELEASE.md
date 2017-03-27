# Release info
Steps for release are
* update version number in develop branch
* update documentation & add changes to changelog
* merge all develop changes to master via pull request
* create release from master branch in github
* release on [pypi](https://pypi.python.org/pypi/sbmlutils)
```
python setup.py sdist upload
```
* switch to develop branch and increase version number
* update zenodo information (DOI & citation)