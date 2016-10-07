#################################################################
# Makefile
#################################################################

build:
    docker build --no-cache --rm --force-rm -t $matthiaskoenig/sbmlutils:latest .

