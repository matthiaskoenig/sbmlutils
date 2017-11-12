# Documentation Builder
The documentation is build based on the resources in this folder using `sphinx`.
To setup the environment install the required dependencies via 
```
cd sbmlutils
workon sbmlutils
(sbmlutils) pip install -e .
(sbmlutils) pip install -r requirements-docs.txt
```

The sbmlutils kernel is needed to execute the notebooks
```
(sbmlutils) python -m ipykernel install --user --name=sbmlutils
```

The documentation can than be build via
```
make html
```
The documentation is written in the `_build` folder which should not be tracked in git.

## Jupter notebooks
An important part of the documentation are the jupyter notebooks in
```
docs_builder/notebooks/
```