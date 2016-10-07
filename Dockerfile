FROM matthiaskoenig/linux-setup-combine:latest
MAINTAINER Matthias Koenig <konigmatt@googlemail.com>

WORKDIR $HOME
RUN pip install cobra --upgrade

# run the tests on source code
RUN git clone https://github.com/matthiaskoenig/sbmlutils
WORKDIR $HOME/sbmlutils
RUN nosetests --with-coverage

# test the installation
RUN python setup.py install

RUN pip install codecov && codecov
RUN bash <(curl -s https://codecov.io/bash)