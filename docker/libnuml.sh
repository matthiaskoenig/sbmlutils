#!/bin/bash
############################################################
# Build libnuml from latest source code
#   https://github.com/NuML/NuML.git
# Usage: 
# 	./libnuml.sh 2>&1 | tee ./logs/libnuml.log
#
############################################################
date
TSTART=`date +%s`

echo "--------------------------------------"
echo "libnuml installation"
echo "--------------------------------------"
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
NUMLCODE=libNuML
SEDMLCODE=libSEDML

GIT_DIR=/git
TMP_DIR=/tmp
# GIT_DIR=/home/mkoenig/git
# TMP_DIR=/home/mkoenig/tmp


echo "--------------------------------------"
echo "pull libNUML repository"
echo "--------------------------------------"
echo "$GIT_DIR/$NUMLCODE"
if [ -d "$GIT_DIR/$NUMLCODE" ]; then
	cd $GIT_DIR/$NUMLCODE
	git pull
else
	cd $GIT_DIR
	git clone https://github.com/NuML/NuML.git $NUMLCODE
	cd $GIT_DIR/$NUMLCODE
fi
echo "*commit*"
git rev-parse HEAD

echo
echo "--------------------------------------"
echo "build libNUML"
echo "--------------------------------------"
NUML_BUILD=$TMP_DIR/numl_build
#if [ -d "$NUML_BUILD" ]; then
#	sudo rm -rf $NUML_BUILD
#fi
mkdir $NUML_BUILD
cd $NUML_BUILD

cmake -DEXTRA_LIBS="xml2;z;bz2;" -DWITH_JAVA=OFF -DWITH_PYTHON=ON -DWITH_R=OFF -DWITH_CPP_NAMESPACE=ON ${GIT_DIR}/$NUMLCODE/libnuml
# cmake -DEXTRA_LIBS="xml2;z;bz2;" -DWITH_JAVA=ON -DWITH_PYTHON=ON -DWITH_R=ON -DPYTHON_EXECUTABLE="/usr/bin/python" -DPYTHON_INCLUDE_DIR="/usr/include/python2.7" -DPYTHON_LIBRARY="/usr/lib/x86_64-linux-gnu/libpython2.7.so" ${GIT_DIR}/$NUMLCODE/libnuml
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

make -j8
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

echo "--------------------------------------"
echo "install libnuml"
echo "--------------------------------------"

# installation
make install
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

