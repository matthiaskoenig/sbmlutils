#!/bin/bash
############################################################
# Build libsbml from latest source
#   http://svn.code.sf.net/p/sbml/code/trunk
#
# Usage: 
# 	./libsbml.sh 2>&1 | tee ./logs/libsbml.log
############################################################
date
TSTART=`date +%s`

echo "--------------------------------------"
echo "libsbml installation"
echo "--------------------------------------"
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SBMLCODE=sbml-code
LIBSBML=libsbml

SVN_DIR=/svn
TMP_DIR=/tmp

echo "--------------------------------------"
echo "build libsbml"
echo "--------------------------------------"
LIBSBML_BUILD=$TMP_DIR/libsbml_build
# if [ -d "$LIBSBML_BUILD" ]; then
#	sudo rm -rf $LIBSBML_BUILD
# fi
mkdir $LIBSBML_BUILD
cd $LIBSBML_BUILD

# cmake -DWITH_BZIP2=OFF -DWITH_ZLIB=OFF -DENABLE_L3V2EXTENDEDMATH=ON -DENABLE_ARRAYS=ON -DENABLE_COMP=ON -DENABLE_DISTRIB=ON -DENABLE_DYN=ON -DENABLE_FBC=ON -DENABLE_GROUPS=ON -DENABLE_LAYOUT=ON -DENABLE_MULTI=ON -DENABLE_QUAL=ON -DENABLE_RENDER=ON -DENABLE_REQUIREDELEMENTS=ON -DENABLE_SPATIAL=ON -DWITH_EXAMPLES=OFF -DWITH_PYTHON=ON -DWITH_CREATE_PYTHON_SOURCE=ON $HOME/svn/sbml-code/libsbml
cmake -DWITH_BZIP2=OFF -DWITH_ZLIB=OFF -DENABLE_L3V2EXTENDEDMATH=ON -DENABLE_ARRAYS=ON -DENABLE_COMP=ON -DENABLE_DISTRIB=ON -DENABLE_DYN=ON -DENABLE_FBC=ON -DENABLE_GROUPS=ON -DENABLE_LAYOUT=ON -DENABLE_MULTI=ON -DENABLE_QUAL=ON -DENABLE_RENDER=ON -DENABLE_REQUIREDELEMENTS=ON -DENABLE_SPATIAL=ON -DWITH_EXAMPLES=OFF -DWITH_PYTHON=ON -DWITH_CREATE_PYTHON_SOURCE=ON ${SVN_DIR}/$SBMLCODE/libsbml
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

make -j8
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

echo "--------------------------------------"
echo "install libsbml"
echo "--------------------------------------"
make install
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi


echo "--------------------------------------"
echo "python bindings"
echo "--------------------------------------"
cd $LIBSBML_BUILD/src/bindings/python/out/
# python setup.py install
python3.6

TEND=`date +%s`
RUNTIME=$((TEND-TSTART))
echo "runtime: $RUNTIME [s]"
