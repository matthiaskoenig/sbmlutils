FROM matthiaskoenig/linux-setup-combine:latest
MAINTAINER Matthias Koenig <konigmatt@googlemail.com>

WORKDIR $HOME
RUN git clone https://github.com/matthiaskoenig/sbmlutils
WORKDIR $HOME/sbmlutils
RUN nosetests