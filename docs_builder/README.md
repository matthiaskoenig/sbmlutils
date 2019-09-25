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

The complete documentation is build via:
```
./make_docs.sh 2>&1 | tee ./make_docs.log
```
This builds the documentation directly from the notebooks.

The HTML documentation can than be build from the files via
```
cd docs_builder
make html
```
The documentation is written in the `_build` folder which should not be tracked in git.

## Jupyter notebooks
An important part of the documentation are the jupyter notebooks in
```
docs_builder/notebooks/
```