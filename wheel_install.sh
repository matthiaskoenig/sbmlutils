#!/usr/bin/env bash
# install the updated dependencies
PY=36
URL=https://github.com/sys-bio/wheelhouse/blob/master
mkdir wheels
wget $URL/tesedml-0.4.3.1-cp36-cp36m-manylinux1_x86_64.whl?raw=true -O wheels/tesedml-0.4.3.1-cp36-cp36m-manylinux1_x86_64.whl
wget $URL/tesbml-5.16.0.0-cp36-cp36m-manylinux1_x86_64.whl?raw=true -O wheels/tesbml-5.16.0.0-cp36-cp36m-manylinux1_x86_64.whl
wget $URL/tecombine-0.2.2.1-cp36-cp36m-manylinux1_x86_64.whl?raw=true -O wheels/tecombine-0.2.2.1-cp36-cp36m-manylinux1_x86_64.whl

pip install wheels/tesbml-5.16.0.0-cp36-cp36m-manylinux1_x86_64.whl
pip install wheels/tesedml-0.4.3.1-cp36-cp36m-manylinux1_x86_64.whl
pip install wheels/tecombine-0.2.2.1-cp36-cp36m-manylinux1_x86_64.whl
