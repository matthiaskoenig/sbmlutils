FROM matthiaskoenig/linux-setup-combine:latest
MAINTAINER Matthias Koenig <konigmatt@googlemail.com>

WORKDIR $HOME
RUN pip install cobra --upgrade

# Install latest tellurium
WORKDIR $HOME
RUN git clone https://github.com/sys-bio/tellurium
WORKDIR $HOME/tellurium

# testing mkoenig branch
RUN git checkout mkoenig
# run tellurium tests
# install latest tellurium
RUN python setup.py install

# run the tests on source code
RUN git clone https://github.com/matthiaskoenig/sbmlutils
WORKDIR $HOME/sbmlutils
RUN nosetests

# test installation
RUN python setup.py install
