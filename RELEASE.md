# Release information

## update documentation
* make necessary updates to notebooks
* build documentation `cd docs_builder` and `./make_docs.sh 2>&1 | tee ./make_docs.log`

## make release
* sort imports (`isort src/sbmlutils`)
* code formating (`black src/sbmlutils`)
* make sure all tests run (`tox --`)
* update release notes in `release-notes`
* bump version (`bumpversion patch` or `bumpversion` minor)
* `git push --tags` (triggers release)
* github: merge develop to master via pull request

* test installation in virtualenv from pypi
```
mkvirtualenv test --python=python3.8
(test) pip install sbmlutils
```


