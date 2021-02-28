# Release information

## update documentation
* build documentation `cd docs_builder` and `make html`

## make release
* update release notes in `release-notes` with commit
* make sure all tests run (`tox -p`)
* bump version (`bumpversion patch` or `bumpversion` minor)
* `git push --tags` (triggers release)

* test installation in virtualenv from pypi
```
mkvirtualenv test --python=python3.8
(test) pip install sbmlutils
```


