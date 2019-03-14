# -----------------------------------------------------------------------------
# Docker image with latest libsbml-experimental python bindings
# -----------------------------------------------------------------------------
# This Dockerfile builds a
# build and run container
#   docker build --tag sbmlutils .
#   docker run --name sbmlutils sbmlutils
#   docker run --name sbmlutils -it sbmlutils bash
# connect pycharm
# settings -> interpreter -> docker -> sbmlutils:latest
# -----------------------------------------------------------------------------
FROM pylibsbml:latest

COPY ./sbmlutils /code/sbmlutils
COPY ./setup.py /code/
COPY ./requirements.txt /code/
COPY ./README.md /code/
COPY ./README.rst /code/
WORKDIR /code
RUN pip install -e .

