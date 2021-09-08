# Release information

## update documentation
* build documentation `cd docs_builder`, `pip install -r requirements.txt` and `make html`

## make release
* update release notes in `release-notes` with commit
* make sure all tests run (`tox -p`)
* bump version (`bumpversion [major|minor|patch]`)
* `git push --tags` (triggers release)

* test installation in virtualenv from pypi
```
mkvirtualenv test --python=python3.8
(test) pip install sbmlutils
```


