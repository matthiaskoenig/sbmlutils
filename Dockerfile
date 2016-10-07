FROM matthiaskoenig/linux-setup-combine:latest
MAINTAINER Matthias Koenig <konigmatt@googlemail.com>

WORKDIR $HOME
RUN pip install cobra --upgrade

# run the tests on source code
RUN git clone https://github.com/matthiaskoenig/sbmlutils
WORKDIR $HOME/sbmlutils
RUN nosetests

# test the installation
RUN python setup.py install