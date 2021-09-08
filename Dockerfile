# -------------------------------------------------------------------------------------
# Container to serve FastAPI backend api from sbmlutils
# -------------------------------------------------------------------------------------
# https://fastapi.tiangolo.com/deployment/docker/
# see https://github.com/tiangolo/uvicorn-gunicorn-docker for env variables

# build image
#   docker build -t myimage .

# start container
#  docker run -d --name mycontainer -p 80:80 -e MODULE_NAME="sbmlutils.report.api" -e VARIABLE_NAME="api" myimage
#  docker run -d --name mycontainer -p 80:80 myimage
# -------------------------------------------------------------------------------------
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Caching of python requirements
COPY ./requirements.txt /code/requirements.txt
CMD pip install --requirement /code/requirements.txt

# Adds application code to the image
# COPY . /code
COPY ./src /code/src
COPY ./setup.cfg /code/setup.cfg
COPY ./setup.py /code/setup.py
COPY ./README.rst /code/README.rst
COPY ./MANIFEST.in /code/MANIFEST.in
COPY ./LICENSE /code/LICENSE

WORKDIR /code

# Install sbmlutils
RUN pip install -e .

ENV MODULE_NAME="sbmlutils.report.api"
ENV VARIABLE_NAME="api"

EXPOSE 80

# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
CMD ["/start.sh"]
