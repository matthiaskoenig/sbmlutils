#!/bin/bash
############################################################
# Build libsedml from latest source code
#   https://github.com/NuML/NuML.git
#	https://github.com/fbergmann/libSEDML.git
#
# Requires NuML.
#
# Usage: 
# 	./libsedml.sh 2>&1 | tee ./logs/libsedml.log
#
############################################################
date
TSTART=`date +%s`

echo "--------------------------------------"
echo "libnuml & libsedml installation"
echo "--------------------------------------"
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
NUMLCODE=libNuML
SEDMLCODE=libSEDML

GIT_DIR=/git
TMP_DIR=/tmp

echo "--------------------------------------"
echo "pull libSEDML repository"
echo "--------------------------------------"
echo "$GIT_DIR/$SEDMLCODE"
if [ -d "$GIT_DIR/$SEDMLCODE" ]; then
	cd $GIT_DIR/$SEDMLCODE
	git pull
else
	cd $GIT_DIR
	git clone https://github.com/fbergmann/libSEDML.git $SEDMLCODE
	cd $GIT_DIR/$SEDMLCODE
fi
echo "*commit*"
git rev-parse HEAD

echo "--------------------------------------"
echo "build libSEDML"
echo "--------------------------------------"
SEDML_BUILD=$TMP_DIR/sedml_build
if [ -d "$SEDML_BUILD" ]; then
    sudo rm -rf $SEDML_BUILD
fi
mkdir $SEDML_BUILD
cd $SEDML_BUILD

cmake -DEXTRA_LIBS="xml2;z;bz2;" -DWITH_EXAMPLES=ON -DWITH_JAVA=OFF -DWITH_PYTHON=ON -DWITH_R=OFF ${GIT_DIR}/$SEDMLCODE
# cmake -DEXTRA_LIBS="xml2;z;bz2;" -DWITH_EXAMPLES=ON -DWITH_JAVA=ON -DWITH_PYTHON=ON -DWITH_R=OFF -DPYTHON_EXECUTABLE="/usr/bin/python" -DPYTHON_INCLUDE_DIR="/usr/include/python2.7" -DPYTHON_LIBRARY="/usr/lib/x86_64-linux-gnu/libpython2.7.so" ${GIT_DIR}/$SEDMLCODE
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

make -j8
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

echo "--------------------------------------"
echo "install libSEDML"
echo "--------------------------------------"

# installation
make install
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

# pythonpath
# echo "Adding to PYTHONPATH: /usr/local/lib/python2.7/site-packages/libsedml"
#cat > libsedml.sh << EOF2
# #!/bin/bash
#export PYTHONPATH=\$PYTHONPATH:/usr/local/lib/python2.7/site-packages/libsedml
# EOF2
# sudo mv libsedml.sh /etc/profile.d/
# source /etc/profile.d/libsedml.sh


TEND=`date +%s`
RUNTIME=$((TEND-TSTART))
echo "runtime: $RUNTIME [s]"