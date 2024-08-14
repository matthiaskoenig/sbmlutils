# -------------------------------------------------------------------------------------
# Container to serve FastAPI backend api from sbmlutils
# -------------------------------------------------------------------------------------
FROM python:3.12

# Add application code to the image
COPY ./src /code/src
COPY ./setup.cfg /code/setup.cfg
COPY ./setup.py /code/setup.py
COPY ./README.rst /code/README.rst
COPY ./MANIFEST.in /code/MANIFEST.in
COPY ./LICENSE /code/LICENSE

WORKDIR /code

# Install sbmlutils
RUN pip install -e . --no-cache-dir --upgrade

#ENV MODULE_NAME="sbmlutils.report.api"
#ENV VARIABLE_NAME="api"
#ENV PORT="1444"

EXPOSE 1444
CMD ["uvicorn", "sbmlutils.report.api:api", "--host", "0.0.0.0", "--port", "1444"]
