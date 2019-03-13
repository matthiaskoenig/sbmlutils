# Docker image with latest libsbml-develop branch python bindings
# build and run container
#   docker build --tag sbmlutils .
#   docker run --name sbmlutils sbmlutils
# connect pycharm
# settings -> interpreter -> docker -> sbmlutils:latest


FROM python:3.6
ENV PYTHONUNBUFFERED 1

# COPY ./sbmlutils /code/sbmlutils
# COPY ./setup.py /code/
# COPY ./requirements.txt /code/
# COPY ./README.md /code/
# COPY ./README.rst /code/
# WORKDIR /code
# RUN pip install -e .

# compile python-libsbml
# pip uninstall -y python-libsbml-experimental

WORKDIR /code
COPY ./libsbml.sh /code/
RUN ./libsbml.sh
