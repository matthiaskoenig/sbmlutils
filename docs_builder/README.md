# Documentation Builder
The documentation is build based on the resources in this folder using `sphinx`.
To setup the environment install the required dependencies via 
```
workon sbmlutils
cd sbmlutils/docs_builder
(sbmlutils) pip install -r requirements-docs.txt
```

The sbmlutils kernel is needed to execute the notebooks
```
(sbmlutils) python -m ipykernel install --user --name=sbmlutils
```
In addition, a pandoc installation is required from https://github.com/jgm/pandoc/releases


## Update notebooks
An important part of the documentation are jupyter notebooks in
```
docs_builder/notebooks/
```
These should be updated before building the documentation.

## Build documentation

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

