# Release information

## update documentation
* build documentation `cd docs_builder` and `./make_docs.sh 2>&1 | tee ./make_docs.log`
* make necessary updates to notebooks

## make release
* sort imports (`isort src/pkdb_analysis`)
* code formating (`black src/pkdb_analysis`)
* make sure all tests run (`tox --`)
* update release notes in `release-notes`
* bump version (`bumpversion patch` or `bumpversion` minor)
* `git push --tags` (triggers release)
* github: merge develop to master via pull request

* test installation in virtualenv from pypi
```
mkvirtualenv test --python=python3.8
(test) pip install sbmlutils --install-option test
```

## version bump
* switch to develop branch and increase version number

